'use strict';

function textFromContent(content) {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';
  return content.map(part => {
    if (!part) return '';
    if (typeof part.text === 'string') return part.text;
    if (typeof part === 'string') return part;
    return '';
  }).filter(Boolean).join('\n');
}

function normalizeMessages(input) {
  if (typeof input === 'string') return [{ role: 'user', content: input }];
  if (!Array.isArray(input)) throw new Error('NIRA_PROVIDER_INPUT_INVALID');
  return input.map(message => ({
    role: message?.role === 'assistant' ? 'assistant' : message?.role === 'system' ? 'system' : 'user',
    content: textFromContent(message?.content)
  })).filter(message => message.content);
}

function classifyFailure(provider, status, detail, retryAfter) {
  const text = String(detail || '');
  const pressure = [429, 502, 503, 504].includes(Number(status));
  const exhausted = Number(status) === 429 &&
    /credit_balance_exhausted|no credits remaining|insufficient[_ -]?quota|billing required|billing|quota exhausted/i.test(text);
  return {
    provider,
    status: Number(status) || 0,
    pressure,
    exhausted,
    retryAfter: Number(retryAfter || 0) || 0,
    detail: text.slice(0, 500)
  };
}

async function callGemini({ input, env, maxOutputTokens, expectJson, fetchFn }) {
  const key = env.GEMINI_API_KEY || '';
  if (!key) return null;
  const model = env.GEMINI_MODEL || 'gemini-3.8-flash';
  const messages = normalizeMessages(input);
  const system = messages.filter(m => m.role === 'system').map(m => m.content).join('\n\n');
  const contents = messages.filter(m => m.role !== 'system').map(m => ({
    role: m.role === 'assistant' ? 'model' : 'user',
    parts: [{ text: m.content }]
  }));
  if (!contents.length) contents.push({ role: 'user', parts: [{ text: 'Return the requested result.' }] });
  const generationConfig = { maxOutputTokens, temperature: 0 };
  if (expectJson) generationConfig.responseMimeType = 'application/json';
  const body = { contents, generationConfig };
  if (system) body.systemInstruction = { parts: [{ text: system }] };
  const response = await fetchFn(
    `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`,
    {
      method: 'POST',
      headers: { 'x-goog-api-key': key, 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }
  );
  if (!response.ok) {
    const detail = await response.text();
    const error = new Error(`GEMINI_HTTP_${response.status}: ${detail.slice(0, 1000)}`);
    error.niraProviderFailure = classifyFailure('gemini', response.status, detail, response.headers.get('retry-after'));
    throw error;
  }
  const result = await response.json();
  const text = (result.candidates || [])
    .flatMap(candidate => candidate?.content?.parts || [])
    .map(part => typeof part?.text === 'string' ? part.text : '')
    .filter(Boolean).join('\n');
  if (!text) throw new Error('GEMINI_EMPTY_RESPONSE');
  return { output_text: text, provider: 'gemini', model };
}

async function callOpenRouter({ input, env, maxOutputTokens, expectJson, fetchFn }) {
  const key = env.OPENROUTER_API_KEY || '';
  if (!key) return null;
  const model = env.OPENROUTER_MODEL || 'openrouter/free';
  const messages = normalizeMessages(input).map(message => ({ role: message.role, content: message.content }));
  const body = {
    model,
    messages,
    max_tokens: maxOutputTokens,
    temperature: 0
  };
  if (expectJson) body.response_format = { type: 'json_object' };
  const response = await fetchFn('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${key}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://github.com/mobinpda-lab/NIRA',
      'X-Title': 'NIRA Autonomous Software Factory'
    },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    const detail = await response.text();
    const error = new Error(`OPENROUTER_HTTP_${response.status}: ${detail.slice(0, 1000)}`);
    error.niraProviderFailure = classifyFailure('openrouter', response.status, detail, response.headers.get('retry-after'));
    throw error;
  }
  const result = await response.json();
  const content = result?.choices?.[0]?.message?.content;
  const text = typeof content === 'string' ? content : Array.isArray(content) ? content.map(part => part?.text || '').filter(Boolean).join('\n') : '';
  if (!text) throw new Error('OPENROUTER_EMPTY_RESPONSE');
  return { output_text: text, provider: 'openrouter', model: result.model || model };
}

async function callOpenAI({ input, env, maxOutputTokens, expectJson, fetchFn }) {
  const key = env.OPENAI_API_KEY || '';
  if (!key) return null;
  const model = env.OPENAI_MODEL || 'gpt-5.6';
  const body = { model, input, max_output_tokens: maxOutputTokens };
  if (expectJson) body.text = { format: { type: 'json_object' } };
  const response = await fetchFn('https://api.openai.com/v1/responses', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    const detail = await response.text();
    const error = new Error(`OPENAI_HTTP_${response.status}: ${detail.slice(0, 1000)}`);
    error.niraProviderFailure = classifyFailure('openai', response.status, detail, response.headers.get('retry-after'));
    throw error;
  }
  const result = await response.json();
  let text = typeof result.output_text === 'string' ? result.output_text : '';
  if (!text) {
    const chunks = [];
    for (const item of (result.output || [])) {
      for (const part of (item.content || [])) {
        if (part.type === 'output_text' && typeof part.text === 'string') chunks.push(part.text);
      }
    }
    text = chunks.join('\n');
  }
  if (!text) throw new Error('OPENAI_EMPTY_RESPONSE');
  return { output_text: text, provider: 'openai', model };
}

function providerMap() {
  return { gemini: callGemini, openrouter: callOpenRouter, openai: callOpenAI };
}

function configuredProviderNames(env) {
  const order = String(env.NIRA_PROVIDER_ORDER || 'gemini,openrouter,openai').split(',').map(value => value.trim().toLowerCase()).filter(Boolean);
  const hasKey = { gemini: Boolean(env.GEMINI_API_KEY), openrouter: Boolean(env.OPENROUTER_API_KEY), openai: Boolean(env.OPENAI_API_KEY) };
  return [...new Set(order)].filter(name => providerMap()[name] && hasKey[name]);
}

function setCoreOutput(core, name, value) {
  if (core && typeof core.setOutput === 'function') core.setOutput(name, String(value));
}

function boundedProviderAttempts(env) {
  const configured = Number(env.NIRA_PROVIDER_ATTEMPTS_PER_PROVIDER || 2);
  if (!Number.isFinite(configured)) return 2;
  return Math.max(1, Math.min(Math.floor(configured), 3));
}

function retryableSameProviderFailure(failure) {
  const status = Number(failure?.status || 0);
  return !failure?.exhausted && (status === 0 || [502, 503, 504].includes(status));
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function routedResponse(input, options = {}) {
  const env = options.env || process.env;
  const core = options.core;
  const fetchFn = options.fetchFn || fetch;
  const maxOutputTokens = Number(options.maxOutputTokens || 12000);
  const expectJson = options.expectJson !== false;
  const providers = configuredProviderNames(env);
  if (!providers.length) {
    setCoreOutput(core, 'provider_pressure', 'false');
    setCoreOutput(core, 'provider_exhausted', 'false');
    setCoreOutput(core, 'provider_active', 'none');
    const error = new Error('NIRA_BLOCKED=NO_AI_PROVIDER_CONFIGURED');
    error.niraProviderMeta = { pressure: false, exhausted: false, status: 0, attempts: [] };
    throw error;
  }

  const attempts = [];
  const calls = providerMap();
  const maxProviderAttempts = boundedProviderAttempts(env);
  for (const provider of providers) {
    for (let providerAttempt = 1; providerAttempt <= maxProviderAttempts; providerAttempt++) {
      try {
        if (core?.notice) core.notice(`NIRA_PROVIDER_ATTEMPT=${provider} attempt=${providerAttempt}/${maxProviderAttempts}`);
        const result = await calls[provider]({ input, env, maxOutputTokens, expectJson, fetchFn });
        if (!result) break;
        setCoreOutput(core, 'provider_pressure', 'false');
        setCoreOutput(core, 'provider_exhausted', 'false');
        setCoreOutput(core, 'provider_status', '200');
        setCoreOutput(core, 'provider_retry_after', '');
        setCoreOutput(core, 'provider_active', provider);
        setCoreOutput(core, 'provider_attempts', attempts.length + 1);
        if (core?.notice) core.notice(`NIRA_PROVIDER_ACTIVE=${provider} model=${result.model || ''}`);
        return result;
      } catch (error) {
        const failure = error.niraProviderFailure || { provider, status: 0, pressure: false, exhausted: false, retryAfter: 0, detail: String(error.message || error).slice(0, 500) };
        attempts.push({ ...failure, providerAttempt });
        const retrySame = providerAttempt < maxProviderAttempts && retryableSameProviderFailure(failure);
        if (retrySame) {
          core?.warning?.(`NIRA_PROVIDER_RETRY provider=${provider} attempt=${providerAttempt}/${maxProviderAttempts} status=${failure.status} bounded=true`);
          await delay(Math.min(1000 * providerAttempt, 2000));
          continue;
        }
        core?.warning?.(`NIRA_PROVIDER_FAILOVER provider=${provider} status=${failure.status} exhausted=${failure.exhausted} pressure=${failure.pressure}`);
        break;
      }
    }
  }

  const pressure = attempts.some(item => item.pressure);
  const exhausted = attempts.length > 0 && attempts.every(item => item.exhausted);
  const last = attempts[attempts.length - 1] || { status: 0, retryAfter: 0 };
  const retryAfter = Math.max(0, ...attempts.map(item => Number(item.retryAfter || 0)));
  setCoreOutput(core, 'provider_pressure', pressure ? 'true' : 'false');
  setCoreOutput(core, 'provider_exhausted', exhausted ? 'true' : 'false');
  setCoreOutput(core, 'provider_status', last.status || 0);
  setCoreOutput(core, 'provider_retry_after', retryAfter || '');
  setCoreOutput(core, 'provider_active', 'none');
  setCoreOutput(core, 'provider_attempts', attempts.length);

  const prefix = exhausted ? 'NIRA_PROVIDER_CAPACITY_EXHAUSTED' : pressure ? `NIRA_PROVIDER_PRESSURE_HTTP_${last.status || 0}` : 'NIRA_PROVIDER_ROUTER_FAILED';
  const error = new Error(`${prefix}: ${attempts.map(item => `${item.provider}:${item.status || 'error'}`).join(',')}`);
  error.niraProviderMeta = { pressure, exhausted, status: last.status || 0, retryAfter, attempts };
  throw error;
}

module.exports = {
  boundedProviderAttempts,
  classifyFailure,
  configuredProviderNames,
  normalizeMessages,
  retryableSameProviderFailure,
  routedResponse
};