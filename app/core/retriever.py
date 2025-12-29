# app/core/retriever.py
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from typing import List, Dict

# استيراد إعداداتنا لضمان استخدام المسارات الصحيحة
from ..config import settings

class Retriever:
    def __init__(self):
        self.model = None
        self.index = None
        self.metadata = None
        self.is_ready = False
        logging.info("تم إنشاء كائن Retriever. يرجى استدعاء .load() للتحميل.")

    def load(self):
        """
        تحميل نموذج التضمين، فهرس FAISS، والبيانات الوصفية.
        هذه عملية ثقيلة يجب أن تتم مرة واحدة عند بدء التشغيل.
        """
        try:
            # --- 1. تحميل نموذج التضمين ---
            model_name = 'paraphrase-multilingual-MiniLM-L12-v2' 
            logging.info(f"بدء تحميل نموذج التضمين: {model_name}")
            self.model = SentenceTransformer(model_name)
            logging.info("تم تحميل نموذج التضمين بنجاح.")

            # --- 2. تحميل فهرس FAISS والبيانات الوصفية ---
            index_path = f"data/index_{settings.INDEX_VERSION}.faiss"
            metadata_path = f"data/metadata_{settings.INDEX_VERSION}.json"
            
            logging.info(f"بدء تحميل فهرس FAISS من: {index_path}")
            self.index = faiss.read_index(index_path)
            logging.info(f"تم تحميل الفهرس بنجاح. عدد المتجهات: {self.index.ntotal}")

            logging.info(f"بدء تحميل البيانات الوصفية من: {metadata_path}")
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logging.info("تم تحميل البيانات الوصفية بنجاح.")

            # التأكد من تطابق عدد السجلات
            if self.index.ntotal != len(self.metadata):
                raise ValueError("عدم تطابق بين عدد المتجهات في الفهرس وعدد السجلات في البيانات الوصفية!")

            self.is_ready = True
            logging.info("--- Retriever جاهز للعمل ---")

        except Exception as e:
            self.is_ready = False
            logging.error(f"فشل في تحميل Retriever: {e}", exc_info=True)
            raise

    def search(self, query: str, k: int = 3) -> List[Dict]:
        """
        البحث عن أكثر k من المستندات صلة باستعلام معين.
        """
        if not self.is_ready:
            raise RuntimeError("Retriever ليس جاهزًا. هل تم استدعاء .load() بنجاح؟")
        
        logging.info(f"بدء البحث عن الاستعلام: '{query}'")
        
        # 1. تحويل الاستعلام إلى متجه
        query_vector = self.model.encode([query], convert_to_tensor=False, normalize_embeddings=True)
        query_vector = np.array(query_vector, dtype='float32')

        # 2. البحث في فهرس FAISS
        # D: distances, I: indices
        distances, indices = self.index.search(query_vector, k)
        
        # 3. تجميع النتائج مع البيانات الوصفية
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            # تجاهل النتائج غير الصحيحة إذا كانت k أكبر من عدد المستندات
            if idx == -1:
                continue
            
            result = self.metadata[idx]
            result['retrieval_score'] = 1 - distances[0][i] # تحويل المسافة إلى درجة تشابه
            results.append(result)
            
        logging.info(f"تم العثور على {len(results)} نتيجة.")
        return results
    
    