# check_models.py
import google.generativeai as genai
from dotenv import load_dotenv
import os

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("لم يتم العثور على متغير البيئة GEMINI_API_KEY")
        
    genai.configure(api_key=api_key)

    print("--- النماذج المتاحة التي تدعم 'generateContent' ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
    print("-------------------------------------------------")

except Exception as e:
    print(f"حدث خطأ: {e}")
    