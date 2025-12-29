# scripts/evaluate_retriever.py
import json
import logging
import sys
import os

# إضافة جذر المشروع إلى مسار بايثون لاستيراد الوحدات بشكل صحيح
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# تعطيل سجلات sentence-transformers المزعجة أثناء التقييم
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

from app.core.retriever import Retriever

# --- إعدادات ---
GOLDEN_SET_PATH = 'evaluation/golden_set.json'
K_FOR_EVALUATION = 3 # سنقوم بالبحث عن أفضل 3 نتائج لكل سؤال

# --- دوال مساعدة لطباعة ملونة ---
def color_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def green(text): return color_text(text, "92")
def red(text): return color_text(text, "91")
def yellow(text): return color_text(text, "93")
def bold(text): return color_text(text, "1")

def evaluate_with_diagnostics():
    """
    يقوم بتقييم محرك الاسترجاع مع طباعة معلومات تشخيصية مفصلة لكل خطوة.
    """
    print(bold("--- بدء تقييم محرك الاسترجاع (مع التشخيص) ---\n"))
    
    # 1. تحميل مجموعة التقييم
    try:
        with open(GOLDEN_SET_PATH, 'r', encoding='utf-8') as f:
            golden_set = json.load(f)
        print(f"✅ تم تحميل {len(golden_set)} سؤال من مجموعة التقييم.")
    except Exception as e:
        print(red(f"❌ فشل في تحميل مجموعة التقييم: {e}"))
        return

    # 2. إعداد المسترجع (Retriever)
    print("⏳ جارٍ تهيئة وتحميل المسترجع...")
    retriever = Retriever()
    retriever.load()
    
    if not retriever.is_ready:
        print(red("❌ فشل في تهيئة المسترجع. إلغاء التقييم."))
        return
    print("✅ المسترجع جاهز للعمل.\n")

    # 3. حساب المقاييس مع التشخيص
    hits_at_1 = 0
    hits_at_k = 0
    total_questions = len(golden_set)
    
    for i, item in enumerate(golden_set):
        question = item['question']
        expected_id = item['expected_id']
        
        print(f"{'='*50}\n{bold(f'CASO DE TESTE #{i+1}')}")
        print(f"  - {bold('Pergunta:')} {question}")
        print(yellow(f"  - {bold('ID esperado:')} {expected_id}"))
        
        # ابحث عن أفضل K نتائج
        results = retriever.search(question, k=K_FOR_EVALUATION)
        retrieved_ids = [res.get('id', 'N/A') for res in results]
        
        print(f"\n  --- {bold('Resultados recuperados (Top K)')} ---")
        if not results:
            print(red("  -> Nenhum resultado retornado."))
        for rank, res in enumerate(results):
            res_id = res.get('id', 'N/A')
            res_score = res.get('retrieval_score', 0.0)
            res_text = res.get('chunk_text', 'No text').replace('\n', ' ')[:80] + "..."
            status_symbol = green("✔") if res_id == expected_id else red("✘")
            print(f"    {rank+1}. ID: {res_id} {status_symbol} | Score: {res_score:.4f} | Text: \"{res_text}\"")
        
        # التقييم
        is_hit_at_1 = len(retrieved_ids) > 0 and retrieved_ids[0] == expected_id
        is_hit_at_k = expected_id in retrieved_ids

        if is_hit_at_1:
            hits_at_1 += 1
            print(green("\n  -> Resultado: HIT @ 1 (A resposta correta está na primeira posição)"))
        elif is_hit_at_k:
            print(yellow("\n  -> Resultado: HIT @ K (A resposta correta está nos resultados, mas não é a primeira)"))
        else:
            print(red("\n  -> Resultado: MISS (A resposta correta não foi encontrada)"))
            
        if is_hit_at_k:
            hits_at_k += 1
            
        print(f"{'='*50}\n")

    # 4. عرض النتائج النهائية
    recall_at_1 = (hits_at_1 / total_questions) * 100
    recall_at_k = (hits_at_k / total_questions) * 100
    
    print(f"\n{'='*20} {bold('RESULTADOS FINAIS')} {'='*20}")
    print(f"  - {bold('Recall@1:')} {recall_at_1:.2f}% ({hits_at_1}/{total_questions} hits)")
    print(f"  - {bold(f'Recall@{K_FOR_EVALUATION}:')} {recall_at_k:.2f}% ({hits_at_k}/{total_questions} hits)")
    
    if recall_at_k >= 85.0:
        print(green(f"\n✅ O critério de sucesso (≥ 85% para Recall@{K_FOR_EVALUATION}) foi alcançado!"))
    else:
        print(red(f"\n⚠️ O critério de sucesso (≥ 85%) não foi alcançado. É necessária uma análise mais aprofundada."))

if __name__ == '__main__':
    evaluate_with_diagnostics()