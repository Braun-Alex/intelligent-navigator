from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import json
import asyncio

from .models import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    EvaluationReportResponse,
    DocumentsListResponse,
    DocumentInfo,
    ParametersResponse,
    ParametersUpdateRequest
)

from app.rag.rag_pipeline import RAGPipeline
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

rag_pipeline: RAGPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Цикл роботи системи"""
    global rag_pipeline

    logger.info("Ініціалізація RAG-системи...")

    try:
        rag_pipeline = RAGPipeline(
            initialize=True,
            use_llm_compression=False,
            use_llm_validation=False
        )
        logger.info("RAG-систему ініціалізовано!")

    except Exception as error:
        logger.error(f"Помилка ініціалізації: {error}")
    
    yield
    
    logger.info("Завершення роботи...")


app = FastAPI(
    title="API-навігатор з нормативних документів КНУТШ",
    description="RAG-система надання відповідей",
    version="3.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/", tags=["General"])
async def root():
    """Кореневий endpoint"""
    return {
        "message": "API-навігатор з нормативних документів КНУТШ",
        "version": "3.1.0",
        "features": ["streaming", "async_evaluation", "validation"],
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Перевірка працездатності системи"""
    vector_store_size = None
    
    if rag_pipeline and rag_pipeline.vector_store:
        try:
            collection = rag_pipeline.vector_store.get()
            vector_store_size = len(collection.get('ids', []))

        except Exception as error:
            logger.warning(f"Помилка при перевірці працездатності системи: {error}")
    
    return HealthResponse(
        status="healthy" if rag_pipeline else "initializing",
        version="3.1.0",
        rag_initialized=rag_pipeline is not None,
        vector_store_size=vector_store_size
    )


@app.get("/query/stream", tags=["RAG"])
async def query_rag_stream(
    question: str,
    return_contexts: bool = True,
    return_evaluation: bool = False
):
    """
    Streaming-обробка запиту користувача через SSE
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG-систему не ініціалізовано!"
        )

    request = QueryRequest(
        question=question,
        return_contexts=return_contexts,
        return_evaluation=return_evaluation
    )
    
    async def event_generator():
        try:
            logger.info(f"Обробка запиту...")
            
            async for event in rag_pipeline.query_stream(
                question=request.question,
                return_evaluation=request.return_evaluation,
                return_contexts=request.return_contexts
            ):
                # Форматуємо як SSE
                event_data = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_data}\n\n"
                
                # Даємо можливість іншим задачам виконуватися
                await asyncio.sleep(0)
            
            # Сигнал завершення
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
            logger.info("Запит успішно оброблено!")

        except Exception as error:
            logger.error(f"Помилка при обробці запиту: {error}")
            error_event = json.dumps({
                "type": "error",
                "data": {"message": str(error)}
            })
            yield f"data: {error_event}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/evaluation/report", response_model=EvaluationReportResponse, tags=["Evaluation"])
async def get_evaluation_report():
    """Надання комплексного звіту стосовно якості відповідей системи"""
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG-систему не ініціалізовано!"
        )
    
    try:
        report = rag_pipeline.get_evaluation_report()
        
        if "message" in report:
            return JSONResponse(status_code=status.HTTP_200_OK, content=report)
        
        return EvaluationReportResponse(**report)
        
    except Exception as error:
        logger.error(f"Помилка при наданні звіту: {error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при наданні звіту: {str(error)}"
        )


@app.get("/documents", response_model=DocumentsListResponse, tags=["Documents"])
async def list_documents():
    """Надання списку документів"""
    try:
        docs_path = Path(settings.documents_path)
        
        if not docs_path.exists():
            return DocumentsListResponse(documents=[], total_documents=0)
        
        documents = []
        for pdf_file in docs_path.glob("*.pdf"):
            file_stat = pdf_file.stat()
            documents.append(DocumentInfo(
                filename=pdf_file.name,
                file_size=file_stat.st_size
            ))
        
        return DocumentsListResponse(
            documents=documents,
            total_documents=len(documents)
        )
        
    except Exception as error:
        logger.error(f"Помилка при наданні списку документів: {error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при наданні списку документів: {str(error)}"
        )


@app.get("/stats", tags=["Statistics"])
async def get_statistics():
    """Надання повної інформації про систему"""
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG-систему не ініціалізовано!"
        )
    
    try:
        stats = rag_pipeline.get_stats()
        
        return {
            "configuration": {
                "embedding_model": settings.embedding_model,
                "llm_model": settings.llm_model,
                "chunk_size": stats["chunk_size"],
                "chunk_overlap": stats["chunk_overlap"],
                "top_k": stats["top_k"],
                "rerank_top_k": stats["rerank_top_k"],
                "bm25_weight": stats["bm25_weight"],
                "vector_weight": stats["vector_weight"],
                "streaming_enabled": True,
                "llm_compression": False,
                "fast_validation": True
            },
            "statistics": {
                "vector_store_size": stats["vector_store_size"],
                "evaluation_enabled": settings.enable_evaluation
            }
        }
        
    except Exception as error:
        logger.error(f"Помилка при наданні статистики: {error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при наданні статистики: {str(error)}"
        )


@app.get("/parameters", response_model=ParametersResponse, tags=["Parameters"])
async def get_parameters():
    """Надання RAG-параметрів системи"""
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG-систему не ініціалізовано!"
        )
    
    try:
        params = rag_pipeline.get_current_parameters()
        return ParametersResponse(**params)

    except Exception as error:
        logger.error(f"Помилка при отриманні параметрів: {error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при отриманні параметрів: {str(error)}"
        )


@app.post("/parameters", tags=["Parameters"])
async def update_parameters(request: ParametersUpdateRequest):
    """Оновлення RAG-параметрів системи"""
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG-систему не ініціалізовано!"
        )
    
    try:
        update_data = request.dict(exclude_unset=True)
        rag_pipeline.update_parameters(update_data)
        new_params = rag_pipeline.get_current_parameters()
        
        return {
            "message": "Параметри успішно оновлено!",
            "status": "success",
            "parameters": new_params
        }
        
    except Exception as error:
        logger.error(f"Помилка оновлення параметрів: {error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка: {str(error)}"
        )


@app.post("/index", tags=["Admin"])
async def index_documents():
    """Індексація документів у сховищі"""
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG-систему не ініціалізовано!"
        )
    
    try:
        logger.info("Початок індексації документів...")
        
        try:
            collection = rag_pipeline.vector_store.get()
            before_count = len(collection.get('ids', []))
        except:
            before_count = 0
        
        rag_pipeline._index_documents()

        try:
            collection = rag_pipeline.vector_store.get()
            after_count = len(collection.get('ids', []))
        except:
            after_count = 0

        if rag_pipeline.retriever:
            rag_pipeline.retriever._build_retrievers()
        
        logger.info(f"Індексацію завершено. Було {before_count}, стало {after_count}")
        
        return {
            "message": "Індексацію успішно виконано!",
            "status": "success",
            "documents_before": before_count,
            "documents_after": after_count,
            "documents_added": after_count - before_count
        }
        
    except Exception as error:
        logger.error(f"Помилка при індексації: {error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при індексації: {str(error)}"
        )


@app.post("/reset", tags=["Admin"])
async def reset_vector_store():
    """Перебудова сховища"""
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG-систему не ініціалізовано!"
        )
    
    try:
        logger.info("Очищення сховища...")
        rag_pipeline.reset_vector_store()
        logger.info("Сховище успішно перебудовано!")
        
        return {
            "message": "Сховище успішно перебудовано!",
            "status": "success"
        }
        
    except Exception as error:
        logger.error(f"Помилка при перебудові: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при перебудові: {str(error)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
