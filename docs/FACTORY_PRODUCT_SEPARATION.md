# قانون تفکیک کارخانه NIRA از پروژه‌ها و محصولات

## 1. هویت رسمی NIRA

**NIRA — سامانه کارخانه نرم‌افزار خودکار و پیوسته گیت‌هاب**

بر اساس سند مرجع جامع NIRA، نیرا یک کارخانه/سامانه برای تولید، کنترل، اعتبارسنجی، انتشار، پایش و بهبود نرم‌افزار است؛ نه محصول وابسته به هیچ‌یک از پروژه‌های مشتری.

## 2. رابطه حاکم

مدل رابطه همیشه این است:

**NIRA (Factory) → Client Project / Product**

استفاده یک پروژه از NIRA برای تولید، تکمیل، بررسی، تست، انتشار یا بهبود، به‌تنهایی هیچ وابستگی معماری یا اجرایی به NIRA ایجاد نمی‌کند.

## 3. استقلال اجباری هر پروژه

هر پروژه مستقل مالک موارد زیر است:

- Repository
- Code
- Architecture
- Data
- Documentation
- Issues
- Pull Requests
- Workflows
- Tests
- Releases
- Product State
- Product Evidence

این موارد نباید صرفاً به دلیل استفاده از NIRA وارد repository یا وضعیت کارخانه شوند.

## 4. تفکیک YadNegar

**YadNegar یک پروژه/محصول مستقل است.**

NIRA فقط کارخانه‌ای است که برای تولید یا تکمیل YadNegar از آن استفاده می‌شود.

بنابراین:

- YadNegar وابسته به NIRA نیست.
- NIRA زیرمجموعه YadNegar نیست.
- تکمیل YadNegar به معنی تکمیل NIRA نیست.
- تکمیل NIRA به معنی تکمیل YadNegar نیست.
- کد و معماری YadNegar نباید با کد و معماری NIRA مخلوط شود.
- اجرای موفق NIRA روی YadNegar فقط می‌تواند به‌عنوان **شاهد توانایی اجرای کارخانه روی یک Client Repository** ثبت شود.

## 5. همین قانون برای همه پروژه‌ها

همین تفکیک برای Arvin، NetworkCenterMonitor و هر پروژه آینده نیز الزامی است.

هر پروژه یک **Client مستقل** است؛ حتی اگر NIRA از ابتدا تا انتشار آن را هدایت یا اجرا کند.

## 6. دو وضعیت کاملاً مستقل

### وضعیت NIRA
گزارش باید فقط شامل موارد مربوط به کارخانه باشد:

- قابلیت‌های کارخانه
- وضعیت Orchestrator / Worker / Queue
- اجرای واقعی
- Evidence
- Cross-Repository Execution
- Blockerهای کارخانه
- Recovery / Self-Fix
- Release و عملیات کارخانه
- بهبود مستمر خود کارخانه

### وضعیت پروژه/محصول
گزارش باید فقط شامل موارد مربوط به همان محصول باشد:

- قابلیت‌های محصول
- وضعیت پیاده‌سازی
- تست و Quality Gate
- Product Validation
- Release
- Blockerهای محصول
- Evidence محصول
- کار باقی‌مانده محصول

## 7. Evidence اجرای بین مخازن

اگر NIRA روی یک پروژه مستقل اجرای واقعی داشته باشد، زنجیره زیر به‌عنوان Evidence کارخانه ثبت می‌شود:

`Issue → Intake → Queue → Lease → Worker → Fencing → Client Branch → Commit → PR → CI → Security → Evidence → Promotion`

این Evidence ثابت می‌کند که کارخانه توانسته روی یک Client Repository کار واقعی انجام دهد؛ اما مالکیت یا استقلال آن پروژه را تغییر نمی‌دهد.

## 8. قوانین گزارش‌دهی

هیچ گزارش، Issue، PR، Workflow یا سندی نباید:

- یک پروژه را «زیرمجموعه NIRA» معرفی کند؛
- وضعیت محصول را به وضعیت کارخانه نسبت دهد؛
- درصد تکمیل محصول را درصد تکمیل NIRA تلقی کند؛
- اجرای NIRA را وابستگی محصول معرفی کند؛
- کد، داده یا تصمیم محصول را بدون دلیل وارد کارخانه کند.

## 9. قانون شروع هر پروژه

در شروع هر پروژه یا موج تکمیل، باید صریحاً مشخص شود:

1. **Client Project:** نام repository هدف
2. **Factory:** NIRA
3. **Relationship:** Factory → Client
4. **Ownership:** متعلق به repository هدف
5. **Scope:** دقیقاً چه چیزی قرار است در پروژه انجام شود
6. **Evidence:** چه شواهدی برای اجرای واقعی لازم است

## 10. اصل‌های نهایی

**Factory completion ≠ Product completion**

**Product completion ≠ Factory completion**

**Factory assistance ≠ Product dependency**

**NIRA execution evidence ≠ Product ownership**

این سند قانون حاکم برای جلوگیری از اختلاط NIRA با YadNegar، Arvin و سایر پروژه‌ها است و باید در شروع، اجرا، گزارش‌دهی، تکمیل و انتشار همه پروژه‌های Client رعایت شود.

---

## مرجع

نام رسمی و مفاهیم این سند بر اساس `docs/NIRA_COMPREHENSIVE_REFERENCE.md` و سند جامع NIRA است. در صورت تعارض، قابلیت عملیاتی قوی‌تر و واقعاً اثبات‌شده NIRA طبق اصل سند مرجع بر متن توضیحی این سند مقدم است.