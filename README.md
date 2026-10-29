# Nova Digital OS — Starter

نسخة بداية قابلة للتشغيل محليًا: موقع عام، استقبال طلبات، لوحة مطوّر محمية، ومساعد AI محلي عبر Ollama.

## المتطلبات
- Python 3.11 أو أحدث
- Ollama اختياري لتجربة مساعد الذكاء الاصطناعي

## التشغيل على Windows
1. فك ضغط المشروع.
2. افتح Terminal داخل مجلد `nova_digital_os`.
3. أنشئ بيئة افتراضية:
   `py -m venv .venv`
4. فعّلها:
   PowerShell: `.venv\\Scripts\\Activate.ps1`
   CMD: `.venv\\Scripts\\activate.bat`
5. ثبّت المتطلبات:
   `pip install -r requirements.txt`
6. انسخ `.env.example` إلى `.env`.
7. عدّل `APP_SECRET` إلى قيمة عشوائية طويلة، وغيّر `ADMIN_PASSWORD` إلى كلمة قوية وفريدة (14 حرفًا على الأقل). لا تشارك ملف `.env`.
   لتوليد سر في Python: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
8. شغّل:
   `uvicorn app:app --reload`
9. افتح `http://127.0.0.1:8000`، ولوحة المطوّر من `http://127.0.0.1:8000/admin`.

## تشغيل مساعد AI محليًا
1. ثبّت Ollama من الموقع الرسمي: https://ollama.com
2. حمّل نموذجًا يناسب جهازك، مثل: `ollama pull llama3.2`
3. تأكد أن Ollama يعمل على `http://127.0.0.1:11434`.
4. تأكد أن `OLLAMA_MODEL` في `.env` يطابق اسم النموذج المثبّت.
5. افتح لوحة المطوّر ثم «مساعد الذكاء الاصطناعي المحلي».

## مهم قبل النشر على الإنترنت
- لا تستخدم `--reload` في الإنتاج.
- فعّل HTTPS واضبط `COOKIE_HTTPS_ONLY=true` خلف HTTPS.
- استخدم قاعدة PostgreSQL مُدارة أو محمية للنسخة الإنتاجية، ونسخًا احتياطية.
- أضف تحديد معدل محاولات تسجيل الدخول على مستوى reverse proxy/WAF، ومراقبة وسجلات، وسياسة خصوصية.
- لا تفتح منفذ Ollama للإنترنت. اجعله محليًا أو خلف شبكة خاصة موثوقة.
- هذه نسخة تأسيسية وليست مراجعة أمنية أو نظامًا إنتاجيًا جاهزًا.
