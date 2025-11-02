from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    """Запит на інформаційний пошук"""
    question: str = Field(..., min_length=1)
    return_contexts: bool = Field(False)
    return_evaluation: bool = Field(False)


class ContextInfo(BaseModel):
    """Інформація про контекст"""
    content: str
    preview: str
    length: int
    metadata: Dict[str, Any]
    source: str
    chunk_index: int
    is_relevant: Optional[bool] = None
    rank: int
    key_terms: List[str]


class EvaluationMetrics(BaseModel):
    """Метрики оцінки якості відповіді"""
    faithfulness: float
    answer_relevancy: float
    context_relevancy: float
    mrr: float
    map: float
    overall_score: float


class QueryResponse(BaseModel):
    """Відповідь на запит"""
    question: str
    answer: str
    num_contexts: int
    contexts: Optional[List[ContextInfo]] = None
    evaluation: Optional[EvaluationMetrics] = None
    validation_failed: Optional[bool] = False
    validation_reason: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check системи"""
    status: str
    version: str
    rag_initialized: bool
    vector_store_size: Optional[int] = None


class EvaluationReportResponse(BaseModel):
    """Звіт оцінки якості системи"""
    total_evaluations: int
    average_metrics: Dict[str, float]
    latest_evaluation: Optional[Dict[str, Any]] = None
    trend: Dict[str, str]


class DocumentInfo(BaseModel):
    """Інформація про документ"""
    filename: str
    file_size: Optional[int] = None


class DocumentsListResponse(BaseModel):
    """Список документів"""
    documents: List[DocumentInfo]
    total_documents: int


class ParametersResponse(BaseModel):
    """Поточні параметри RAG"""
    chunk_size: int
    chunk_overlap: int
    top_k: int
    rerank_top_k: int
    bm25_weight: float
    vector_weight: float


class ParametersUpdateRequest(BaseModel):
    """Запит на оновлення параметрів RAG"""
    chunk_size: Optional[int] = Field(None, ge=128, le=2048)
    chunk_overlap: Optional[int] = Field(None, ge=32, le=512)
    top_k: Optional[int] = Field(None, ge=1, le=20)
    rerank_top_k: Optional[int] = Field(None, ge=1, le=15)
    bm25_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    vector_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
