# Dockerfile

# --- المرحلة الأولى: البناء (Builder Stage) ---
# نستخدم صورة كاملة لتثبيت الاعتماديات مع أدوات البناء اللازمة
FROM python:3.10-slim AS builder

# تحديد متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تعيين مجلد العمل
WORKDIR /app

# تثبيت الاعتماديات في بيئة افتراضية
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# نسخ ملف المتطلبات وتثبيت الحزم
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- المرحلة الثانية: النهائية (Final Stage) ---
# نستخدم صورة "slim" صغيرة لتقليل حجم الصورة النهائية
FROM python:3.10-slim

# تحديد متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# إنشاء مستخدم غير جذري (non-root) لزيادة الأمان
RUN addgroup --system app && adduser --system --group app

# تعيين مجلد العمل
WORKDIR /home/app

# نسخ البيئة الافتراضية من مرحلة البناء
COPY --from=builder /opt/venv /opt/venv

# نسخ كود التطبيق ومجلدات البيانات اللازمة
COPY --chown=app:app app ./app
COPY --chown=app:app data ./data
COPY --chown=app:app knowledge_base ./knowledge_base

# تعيين المستخدم غير الجذري
USER app

# تحديد المسار للبيئة الافتراضية
ENV PATH="/opt/venv/bin:$PATH"

# الأمر لتشغيل التطبيق
# نستخدم 0.0.0.0 للسماح بالاتصالات من خارج الحاوية
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

