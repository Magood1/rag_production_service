# scripts/ingest.py
import os
import json
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
import logging

# إعداد التسجيل (Logging) لمتابعة العملية
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. الإعدادات والمتغيرات الأساسية ---
# اسم النموذج المستخدم لإنشاء المتجهات. اختياره حاسم لجودة البحث.
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2' 

# مسار ملف قاعدة المعرفة
KNOWLEDGE_BASE_PATH = 'knowledge_base/faq.json'

# مسارات حفظ المخرجات (الفهرس والبيانات الوصفية)
OUTPUT_DIR = 'data'
INDEX_PATH = os.path.join(OUTPUT_DIR, 'index_v1.faiss')
METADATA_PATH = os.path.join(OUTPUT_DIR, 'metadata_v1.json')

def create_output_directory():
    """ينشئ مجلد المخرجات إذا لم يكن موجودًا."""
    if not os.path.exists(OUTPUT_DIR):
        logging.info(f"إنشاء مجلد المخرجات: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

def ingest_and_build_index():
    """
    الوظيفة الرئيسية التي تقوم بقراءة البيانات، إنشاء المتجهات، وبناء فهرس FAISS.
    """
    logging.info("--- بدء عملية استيعاب البيانات وبناء الفهرس ---")
    
    # --- 2. قراءة ومعالجة البيانات ---
    try:
        df = pd.read_json(KNOWLEDGE_BASE_PATH)
        logging.info(f"تم تحميل {len(df)} سجل من قاعدة المعرفة.")
    except Exception as e:
        logging.error(f"فشل في تحميل قاعدة المعرفة: {e}")
        return

    # استراتيجية التقسيم (Chunking): دمج السؤال والجواب في نص واحد للبحث الدلالي
    # هذا يضمن أن معنى السؤال والجواب مرتبطان في متجه واحد.
    df['chunk_text'] = df.apply(lambda row: f"سؤال: {row['question']} جواب: {row['answer']}", axis=1)
    
    texts_to_embed = df['chunk_text'].tolist()
    metadata = df.to_dict(orient='records')

    # --- 3. تحميل نموذج التضمين ---
    logging.info(f"تحميل نموذج SentenceTransformer: {MODEL_NAME}")
    # سيتم تنزيل النموذج تلقائيًا في المرة الأولى وتخزينه مؤقتًا.
    model = SentenceTransformer(MODEL_NAME)

    # --- 4. إنشاء المتجهات (Embeddings) ---
    logging.info("بدء إنشاء المتجهات للنصوص... هذه العملية قد تستغرق بعض الوقت.")
    embeddings = model.encode(texts_to_embed, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype='float32')
    logging.info(f"تم إنشاء {len(embeddings)} متجه. أبعاد المتجه الواحد: {embeddings.shape[1]}")

    # --- 5. بناء وحفظ فهرس FAISS ---
    index_dimension = embeddings.shape[1]
    # استخدام IndexFlatL2: يقوم ببحث دقيق (exact search)، وهو مثالي للبداية ومجموعات البيانات الصغيرة.
    index = faiss.IndexFlatL2(index_dimension)
    
    logging.info("إضافة المتجهات إلى فهرس FAISS.")
    index.add(embeddings)
    
    logging.info(f"حفظ فهرس FAISS في المسار: {INDEX_PATH}")
    faiss.write_index(index, INDEX_PATH)
    
    # --- 6. حفظ البيانات الوصفية (Metadata) ---
    # نحفظ البيانات الوصفية في ملف منفصل. ترتيب السجلات هنا يطابق تمامًا
    # ترتيب المتجهات في فهرس FAISS (مهم جدًا).
    logging.info(f"حفظ البيانات الوصفية في المسار: {METADATA_PATH}")
    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
        
    logging.info(f"--- اكتملت العملية بنجاح! ---")
    logging.info(f"عدد المتجهات في الفهرس: {index.ntotal}")

if __name__ == '__main__':
    create_output_directory()
    ingest_and_build_index()

    