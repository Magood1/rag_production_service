# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    # متغيرات مطلوبة؛ سيفشل التطبيق إذا لم تكن موجودة في البيئة.
    GEMINI_API_KEY: str
    INDEX_VERSION: str

    # متغيرات اختيارية مع قيم افتراضية
    LOG_LEVEL: str = "INFO"

    # تحديد مصدر الإعدادات (ملف .env ومتغيرات البيئة)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# إنشاء نسخة واحدة من الإعدادات ليتم استيرادها في جميع أنحاء التطبيق
settings = AppSettings()

