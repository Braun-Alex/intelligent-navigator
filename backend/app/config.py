from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Налаштування системи"""
    
    # Конфігурація OpenAI
    openai_api_key: str
    llm_model: str = "gpt-5-nano"
    
    # Конфігурація моделей
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Конфігурація RAG
    chunk_size: int = 512
    chunk_overlap: int = 128
    top_k: int = 5
    rerank_top_k: int = 3
    bm25_weight: float = 0.3
    vector_weight: float = 0.7
    
    # Конфігурація сховища
    persist_directory: str = "./chroma_db"
    collection_name: str = "knu_documents"
    
    # Розташування теки з документами
    documents_path: str = "./documents"
    
    # Оцінка якості системи
    enable_evaluation: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
