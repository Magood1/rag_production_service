# tests/test_api.py
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

@patch('app.main.retriever_instance')
@patch('app.main.generate_answer')
def test_ask_question_success(mock_generate_answer, mock_retriever_instance):
    """اختبار المسار الناجح لنقطة النهاية /api/v1/ask."""
    # إعداد المخرجات الوهمية (Mocks)
    mock_retriever_instance.search.return_value = [
        {"id": "test-001", "source": "test.pdf", "retrieval_score": 0.9}
    ]
    mock_generate_answer.return_value = {
        "answer": "هذه إجابة وهمية.",
        "confidence_score": 0.9
    }

    # استدعاء نقطة النهاية
    response = client.post("/api/v1/ask?query=test&k=1")

    # التحقق من النتائج
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "هذه إجابة وهمية."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["id"] == "test-001"
    mock_retriever_instance.search.assert_called_once_with("test", k=1)
    mock_generate_answer.assert_called_once()