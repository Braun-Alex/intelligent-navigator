import os
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pypdf
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.rag.retriever.hybrid_retriever import HybridRetriever
from app.rag.evaluator.quality_evaluator import RAGQualityEvaluator
from app.rag.validator.query_validator import QueryValidator
from app.rag.prompts.prompt_templates import answer_generation_prompt
from app.rag.splitter.custom_splitter import HybridLegalDocumentSplitter


class RAGPipeline:
    """
    RAG-пайплайн з підтримкою:
    - streaming-режимом відповідей
    - асинхронної оцінки якості
    - валідації запитів
    - опціонального LLM compression
    """

    def __init__(
            self,
            documents_path: Optional[str] = None,
            persist_directory: Optional[str] = None,
            initialize: bool = True,
            use_llm_compression: bool = False,
            use_llm_validation: bool = False
    ):
        self.documents_path = documents_path or settings.documents_path
        self.persist_directory = persist_directory or settings.persist_directory

        # Параметри RAG
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.top_k = min(settings.top_k, 5)
        self.rerank_top_k = min(settings.rerank_top_k, 3)
        self.bm25_weight = settings.bm25_weight
        self.vector_weight = settings.vector_weight
        self.use_llm_compression = use_llm_compression
        self.cross_encoder_model = settings.cross_encoder_model

        # Thread Pool для асинхронних задач
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Ініціалізація вбудовувань
        print("Ініціалізація вбудовувань...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Ініціалізація LLM
        print("Ініціалізація LLM...")
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.0,
            openai_api_key=settings.openai_api_key,
            streaming=True
        )

        # Компоненти RAG
        self.vector_store = None
        self.retriever = None
        self.evaluator = None
        self.query_validator = None

        if initialize:
            self._initialize_pipeline(use_llm_validation)

    def _initialize_pipeline(self, use_llm_validation: bool = False):
        """Ініціалізація RAG-пайплайну"""
        if os.path.exists(self.persist_directory):
            print("Завантаження наявного сховища...")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name=settings.collection_name
            )

            try:
                collection = self.vector_store.get()
                doc_count = len(collection.get('ids', []))
                print(f"Знайдено {doc_count} чанків у сховищі!")

                if doc_count == 0:
                    print("Сховище є порожнім. Початок індексації документів...")
                    self._index_documents()

            except Exception as error:
                print(f"Помилка перевірки сховища: {error}")
                print("Повторна переіндексація документів...")
                self._index_documents()
        else:
            print("Створення нового сховища...")
            self._create_vector_store()

        # Ініціалізація гібридного ретривера
        print("Ініціалізація гібридного ретривера...")
        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            embeddings=self.embeddings,
            llm=None,
            bm25_weight=self.bm25_weight,
            vector_weight=self.vector_weight,
            top_k=self.top_k,
            rerank_top_k=self.rerank_top_k,
            use_llm_compression=False,
            cross_encoder_model=self.cross_encoder_model
        )

        # Ініціалізація оцінювача якості
        if settings.enable_evaluation:
            print("Ініціалізація оцінювача якості відповідей...")
            self.evaluator = RAGQualityEvaluator(llm=self.llm)

        # Ініціалізація валідатора запитів
        print("Ініціалізація валідатора запитів...")
        self.query_validator = QueryValidator(
            llm=self.llm,
            use_llm_validation=use_llm_validation
        )

        self.prompt_template = answer_generation_prompt

        print("RAG-пайплайн ініціалізовано успішно!")

    def _create_vector_store(self):
        """Створення сховища з PDF-документів"""
        documents = self._load_documents()

        if not documents:
            raise ValueError("Не знайдено жодних документів!")

        print("Розбиття тексту документів за допомогою гібридного розбивача...")

        hybrid_splitter = HybridLegalDocumentSplitter(
            embeddings=self.embeddings,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        splits = hybrid_splitter.split_documents(documents)
        print(f"Створено {len(splits)} чанків документів!")

        # Створення сховища
        self.vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name=settings.collection_name
        )

        print(f"Сховище створено з {len(splits)} чанками!")

    def _load_documents(self) -> List[Document]:
        """Завантаження PDF-документів"""
        documents = []
        docs_path = Path(self.documents_path)

        if not docs_path.exists():
            print(f"Шлях {self.documents_path} до документу не існує!")
            return documents

        pdf_files = list(docs_path.glob("*.pdf"))
        print(f"Знайдено {len(pdf_files)} PDF-файлів!")

        for pdf_file in pdf_files:
            try:
                with open(pdf_file, 'rb') as file:
                    reader = pypdf.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n\n"

                doc = Document(
                    page_content=text,
                    metadata={"source": pdf_file.name, "pages": len(reader.pages)}
                )

                documents.append(doc)
                print(f"Завантажено {pdf_file.name}: {len(reader.pages)} сторінок")

            except Exception as error:
                print(f"Помилка завантаження {pdf_file.name}: {error}")

        return documents

    def _index_documents(self):
        """Індексація документів у сховищі з перевіркою на дублікати"""
        try:
            documents = self._load_documents()

            if not documents:
                print("Документів для індексації не знайдено!")
                return

            # Отримуємо список вже проіндексованих документів
            indexed_sources = set()
            try:
                collection = self.vector_store.get()
                if collection and 'metadatas' in collection:
                    for metadata in collection['metadatas']:
                        if metadata and 'source' in metadata:
                            indexed_sources.add(metadata['source'])
                print(f"Знайдено {len(indexed_sources)} унікальних документів у сховищі!")

            except Exception as error:
                print(f"Не вдалося отримати список проіндексованих документів: {error}")

            # Фільтруємо тільки нові документи
            new_documents = []
            skipped_documents = []
            for doc in documents:
                source = doc.metadata.get('source', '')
                if source not in indexed_sources:
                    new_documents.append(doc)
                else:
                    skipped_documents.append(source)

            if skipped_documents:
                print(
                    f"Пропущено {len(skipped_documents)} вже проіндексованих документів: {', '.join(skipped_documents)}")

            if not new_documents:
                print("Немає нових документів для індексації!")
                return

            print(f"Знайдено {len(new_documents)} нових документів для індексації!")

            print("Розбиття тексту документів за допомогою гібридного розбивача...")

            hybrid_splitter = HybridLegalDocumentSplitter(
                embeddings=self.embeddings,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )

            splits = hybrid_splitter.split_documents(new_documents)
            print(f"Створено {len(splits)} чанків з нових документів!")

            # Додавання чанків до сховища
            if self.vector_store:
                print(f"Додавання {len(splits)} чанків до сховища...")
                self.vector_store.add_documents(splits)
                print(f"Успішно проіндексовано {len(splits)} чанків з {len(new_documents)} нових документів!")
            else:
                print("Помилка: сховище не ініціалізовано")

        except Exception as error:
            print(f"Помилка індексації документів: {error}")
            import traceback
            traceback.print_exc()

    async def query_stream(
            self,
            question: str,
            return_evaluation: bool = False,
            return_contexts: bool = False
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Метод запиту до RAG-системи
        """
        # Валідація запиту
        if self.query_validator:
            validation_result = self.query_validator.validate_query(question)
            
            yield {
                "type": "validation",
                "data": {
                    "is_valid": validation_result.is_valid,
                    "reason": validation_result.rejection_reason
                }
            }

            if not validation_result.is_valid:
                return

        # Отримання контекстів
        retrieved_results = self.retriever.retrieve(question, return_scores=True)
        retrieved_docs = [r.document for r in retrieved_results]

        # Підготовка контексту
        context_text = "\n\n---\n\n".join([
            f"[Джерело: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
            for doc in retrieved_docs
        ])

        if return_contexts:
            key_terms = self.retriever._extract_key_terms(question)
            contexts_data = []
            
            for i, result in enumerate(retrieved_results):
                doc = result.document
                contexts_data.append({
                    "content": doc.page_content,
                    "preview": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    "length": len(doc.page_content),
                    "metadata": doc.metadata,
                    "source": doc.metadata.get('source', 'Unknown'),
                    "chunk_index": doc.metadata.get('chunk_index', None),
                    "rank": i + 1,
                    "key_terms": key_terms
                })

            yield {
                "type": "contexts",
                "data": {
                    "contexts": contexts_data,
                    "num_contexts": len(contexts_data)
                }
            }

        # Генерація відповіді
        prompt = self.prompt_template.format(
            context=context_text,
            question=question
        )

        full_answer = ""
        async for chunk in self.llm.astream(prompt):
            token = chunk.content
            full_answer += token
            
            yield {
                "type": "token",
                "data": {"token": token}
            }

        # Асинхронна оцінка якості
        if return_evaluation and self.evaluator:
            # Потокове оцінювання якості
            loop = asyncio.get_event_loop()
            evaluation_task = loop.run_in_executor(
                self.executor,
                self._evaluate_async,
                question,
                full_answer,
                retrieved_docs
            )

            yield {
                "type": "evaluation_pending",
                "data": {"message": "Відбувається оцінка якості відповіді..."}
            }
            
            # Коли оцінка є готовою, відправляємо результат
            try:
                metrics = await evaluation_task
                yield {
                    "type": "evaluation",
                    "data": {
                        "faithfulness": metrics.faithfulness,
                        "answer_relevancy": metrics.answer_relevancy,
                        "context_relevancy": metrics.context_relevancy,
                        "mrr": metrics.mrr,
                        "map": metrics.map_score,
                        "overall_score": metrics.overall_score
                    }
                }
            except Exception as error:
                print(f"Помилка оцінки якості: {error}")
                yield {
                    "type": "evaluation_error",
                    "data": {"error": str(error)}
                }

    def _evaluate_async(self, query: str, answer: str, contexts: List[Document]):
        """Синхронна функція для виконання в Thread Pool"""
        return self.evaluator.evaluate(
            query=query,
            answer=answer,
            contexts=contexts
        )

    def __del__(self):
        """Закриття Thread Pool при завершенні роботи"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

    def get_stats(self) -> Dict[str, Any]:
        """Надання повної інформації про систему"""
        stats = {
            "vector_store_size": 0,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "rerank_top_k": self.rerank_top_k,
            "bm25_weight": self.bm25_weight,
            "vector_weight": self.vector_weight
        }

        if self.vector_store:
            try:
                collection = self.vector_store._collection
                stats["vector_store_size"] = collection.count()

            except:
                pass

        return stats

    def get_current_parameters(self) -> Dict[str, Any]:
        """Надання RAG-параметрів системи"""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "rerank_top_k": self.rerank_top_k,
            "bm25_weight": self.bm25_weight,
            "vector_weight": self.vector_weight
        }

    def update_parameters(self, parameters: Dict[str, Any]):
        """Оновлення RAG-параметрів системи"""
        if "chunk_size" in parameters:
            self.chunk_size = parameters["chunk_size"]
        if "chunk_overlap" in parameters:
            self.chunk_overlap = parameters["chunk_overlap"]
        if "top_k" in parameters:
            self.top_k = parameters["top_k"]
        if "rerank_top_k" in parameters:
            self.rerank_top_k = parameters["rerank_top_k"]
        if "bm25_weight" in parameters:
            self.bm25_weight = parameters["bm25_weight"]
        if "vector_weight" in parameters:
            self.vector_weight = parameters["vector_weight"]

        # Переініціалізація ретривера
        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            embeddings=self.embeddings,
            llm=self.llm if self.use_llm_compression else None,
            bm25_weight=self.bm25_weight,
            vector_weight=self.vector_weight,
            top_k=self.top_k,
            rerank_top_k=self.rerank_top_k,
            use_llm_compression=self.use_llm_compression,
            cross_encoder_model=self.cross_encoder_model
        )

        print(f"Параметри оновлено: {parameters}")

    def reset_vector_store(self):
        """Перебудова сховища"""
        import time
        import gc

        print("Очищення сховища через ChromaDB API...")

        # Видалення колекції через ChromaDB API
        try:
            if self.vector_store:
                chroma_client = self.vector_store._client
                collection_name = settings.collection_name

                print(f"Видалення колекції '{collection_name}'...")

                try:
                    chroma_client.delete_collection(name=collection_name)
                    print(f"Колекцію '{collection_name}' успішно видалено!")

                except Exception as error:
                    print(f"Попередження при видаленні колекції: {error}")

                # Закриття з'єднання
                del self.vector_store
                self.vector_store = None

                # Очищення ресурсів
                gc.collect()
                time.sleep(0.5)

        except Exception as error:
            print(f"Помилка при роботі з ChromaDB API: {error}")
            # Fallback: спробуємо просто очистити об'єкт
            self.vector_store = None
            gc.collect()
            time.sleep(0.5)

        # Створюємо нове сховище
        print("Створення нового сховища...")
        self._create_vector_store()

        print("Переініціалізація ретривера...")
        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            embeddings=self.embeddings,
            llm=self.llm if self.use_llm_compression else None,
            bm25_weight=self.bm25_weight,
            vector_weight=self.vector_weight,
            top_k=self.top_k,
            rerank_top_k=self.rerank_top_k,
            use_llm_compression=self.use_llm_compression,
            cross_encoder_model=self.cross_encoder_model
        )

        print("Сховище успішно перебудовано!")

    def get_evaluation_report(self) -> Dict[str, Any]:
        """Надання комплексного звіту стосовно якості відповідей системи"""
        if not self.evaluator:
            return {"message": "Оцінку якості системи не ввімкнено"}

        return self.evaluator.get_evaluation_report()

    def add_documents(self, documents: List[Document]):
        """Додавання нових чанків"""
        hybrid_splitter = HybridLegalDocumentSplitter(
            embeddings=self.embeddings,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        splits = hybrid_splitter.split_documents(documents)
        self.vector_store.add_documents(splits)

        # Перебудова ретриверів
        if self.retriever:
            self.retriever._build_retrievers()

        print(f"Додано {len(splits)} чанків!")
