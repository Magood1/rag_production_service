# app/main.py (النسخة النهائية والمُدققة - جاهزة للنشر)

from contextlib import asynccontextmanager
import logging
import time
import uuid
from typing import Optional, List, Any, Dict

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse  # <-- تمت إعادته
from pydantic import BaseModel, Field

from .config import settings
from .core.retriever import Retriever
from .core.generator import generate_answer

# --- إعدادات التسجيل ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("rag_service")

# --- متغيرات عامة ---
retriever_instance: Optional[Retriever] = None

# --- دورة حياة التطبيق ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever_instance
    logger.info("--- بدء تحميل الموارد عند بدء التشغيل ---")
    try:
        retriever_instance = Retriever()
        retriever_instance.load()
        logger.info("تم تحميل المسترجع بنجاح.")
    except Exception as e:
        logger.exception("فشل فادح في تهيئة المسترجع عند بدء التشغيل: %s", e)
    yield
    logger.info("--- إغلاق الموارد عند إيقاف التشغيل ---")

# --- تطبيق FastAPI ---
app = FastAPI(
    title="Production-Grade RAG Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# --- نماذج Pydantic ---
class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    index_version: str
    retriever_ready: bool

class Source(BaseModel):
    id: str
    source: str
    retrieval_score: float

class RAGResponse(BaseModel):
    request_id: str
    answer: str
    confidence_score: float = Field(..., ge=0, le=1)
    sources: List[Source]
    timings: Dict[str, float]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# --- Middleware ---
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ✨ --- تمت إعادته: معالج الأخطاء العام الحيوي --- ✨
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("خطأ غير معالج (request_id=%s): %s", request_id, exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=f"request_id={request_id}"
        ).model_dump()
    )

# --- نقاط النهاية (Endpoints) ---
@app.get("/healthz", tags=["Monitoring"], response_model=HealthResponse)
def health_check():
    is_retriever_ready = bool(retriever_instance and getattr(retriever_instance, "is_ready", False))
    return HealthResponse(
        status="ok",
        index_version=settings.INDEX_VERSION,
        retriever_ready=is_retriever_ready
    )

@app.post(
    "/api/v1/ask",
    tags=["RAG"],
    response_model=RAGResponse,
    summary="اطرح سؤالاً على وكيل الدعم الذكي"
)
def ask_question(
    request: Request,
    query: str = Query(..., min_length=3, max_length=512, description="السؤال المراد طرحه"),
    k: int = Query(3, ge=1, le=5, description="عدد المصادر المراد استرجاعها")
):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    if retriever_instance is None or not retriever_instance.is_ready:
        logger.warning("المسترجع غير جاهز (request_id=%s)", request_id)
        raise HTTPException(status_code=503, detail="Service not ready: Retriever is unavailable.")

    full_start_time = time.perf_counter()

    # 1. مرحلة الاسترجاع
    retrieval_start = time.perf_counter()
    context_chunks = retriever_instance.search(query, k=k)
    retrieval_end = time.perf_counter()

    # 2. مرحلة التوليد
    generation_start = time.perf_counter()
    generated_data = generate_answer(query=query, context_chunks=context_chunks)
    generation_end = time.perf_counter()

    full_end_time = time.perf_counter()

    # 3. تجميع الاستجابة
    timings = {
        "retrieval_ms": (retrieval_end - retrieval_start) * 1000,
        "generation_ms": (generation_end - generation_start) * 1000,
        "total_ms": (full_end_time - full_start_time) * 1000
    }

    logger.info("تمت معالجة الطلب (request_id=%s) بنجاح. التوقيتات: %s", request_id, timings)

    # بناء قائمة المصادر مباشرة من نتائج المسترجع
    response_sources = [Source(**c) for c in context_chunks]

    return RAGResponse(
        request_id=request_id,
        answer=generated_data["answer"],
        confidence_score=generated_data["confidence_score"],
        sources=response_sources,
        timings=timings
    )
