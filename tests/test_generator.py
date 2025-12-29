#tests/test_generator.py


from app.core.generator import build_prompt
def test_build_prompt_structure():
    """اختبار أن الموجه يحتوي على الأقسام الرئيسية."""
    query = "سؤالي"
    context = [{"chunk_text": "نص السياق"}]
    prompt = build_prompt(query, context)

    assert "السياق:" in prompt
    assert "نص السياق" in prompt
    assert "السؤال: سؤالي" in prompt
    assert "الإجابة:" in prompt

    