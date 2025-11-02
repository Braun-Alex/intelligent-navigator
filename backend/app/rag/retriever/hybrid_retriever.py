import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from langchain_core.language_models import BaseLLM
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainFilter
from dataclasses import dataclass
from sentence_transformers import CrossEncoder

from app.config import settings


@dataclass
class RetrievalResult:
    """Результат інформаційного пошуку"""
    document: Document
    relevance_score: float
    rank: int


class HybridRetriever:
    """
    Гібридний ретривер на основі LangChain's EnsembleRetriever, що комбінує розріджений BM25-пошук і щільний векторний пошук
    """

    def __init__(
            self,
            vector_store: Chroma,
            embeddings: Optional[Embeddings] = None,
            llm: Optional[BaseLLM] = None,
            bm25_weight: float = 0.3,
            vector_weight: float = 0.7,
            top_k: int = 5,
            rerank_top_k: int = 3,
            use_llm_compression: bool = True,
            cross_encoder_model: str = settings.cross_encoder_model
    ):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.llm = llm
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k
        self.use_llm_compression = use_llm_compression and llm is not None

        # Ініціалізація ретриверів
        self.bm25_retriever = None
        self.vector_retriever = None
        self.ensemble_retriever = None
        self.compression_retriever = None
        self.cross_encoder = None

        # Побудова індексів
        self._build_retrievers()

        print("Ініціалізація крос-енкодера...")

        try:
            self.cross_encoder = CrossEncoder(cross_encoder_model)

        except Exception as error:
            print(f"Не вдалося завантажити крос-ендокер: {error}. Re-ranking відбуватиметься без використання крос-ендокера")
            self.cross_encoder = None

    def _build_retrievers(self):
        """Побудова BM25 і векторного ретриверів з документів у сховищі"""
        try:
            all_docs = self.vector_store.get(include=['documents', 'metadatas'])

            if all_docs and 'documents' in all_docs and all_docs['documents']:
                valid_docs = []

                metadatas = all_docs.get('metadatas', [{} for _ in all_docs['documents']])

                for i, doc_text in enumerate(all_docs['documents']):
                    if doc_text and isinstance(doc_text, str) and doc_text.strip():
                        # Токенізація для BM25
                        tokens = re.findall(r'\w+', doc_text.lower())
                        if tokens:
                            valid_docs.append(Document(page_content=doc_text, metadata=metadatas[i]))

                if valid_docs:
                    # BM25-ретривер
                    self.bm25_retriever = BM25Retriever.from_documents(valid_docs)
                    self.bm25_retriever.k = self.top_k * 2

                    # Векторний ретривер
                    self.vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": self.top_k * 2})

                    # Ensemble-ретривер
                    self.ensemble_retriever = EnsembleRetriever(
                        retrievers=[self.bm25_retriever, self.vector_retriever],
                        weights=[self.bm25_weight, self.vector_weight]
                    )

                    # LLM compression
                    if self.use_llm_compression:
                        compressor = LLMChainFilter.from_llm(self.llm)
                        self.compression_retriever = ContextualCompressionRetriever(
                            base_compressor=compressor,
                            base_retriever=self.ensemble_retriever
                        )

                    print(f"Гібридний ретривер успішно ініціалізовано!")
                else:
                    print("Не знайдено валідних документів!")
            else:
                print("Сховище є порожнім!")

        except Exception as error:
            print(f"Не вдалося побудувати гібридний ретривер: {error}")
            import traceback
            traceback.print_exc()

    def _cross_encoder_rerank(self, query: str, documents: List[Document]) -> List[Tuple[Document, float]]:
        """Re-ranking з використанням крос-енкодера для досягнення кращої семантичної релевантності"""
        if not self.cross_encoder or not documents:
            return [(doc, 0.0) for doc in documents]

        pairs = [[query, doc.page_content] for doc in documents]
        scores = self.cross_encoder.predict(pairs)
        sorted_docs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return sorted_docs

    def _extract_key_terms(self, query: str) -> List[str]:
        """Екстракція ключових термінів із запиту з використанням крос-енкодера для семантичної релевантності"""

        stop_words = {
            'авжеж', 'адже', 'але', 'б', 'без', 'був', 'була', 'були', 'було', 'бути', 'більш', 'вам', 'вас',
            'весь', 'вздовж', 'ви', 'вниз', 'внизу', 'вона', 'вони', 'воно', 'все', 'всередині', 'всіх', 'від',
            'він', 'да', 'давай', 'давати', 'де', 'дещо', 'для', 'до', 'з', 'завжди', 'замість', 'й', 'коли',
            'ледве', 'майже', 'ми', 'навколо', 'навіть', 'нам', 'от', 'отже', 'отож', 'поза', 'про', 'під', 'та',
            'так', 'такий', 'також', 'те', 'ти', 'тобто', 'тож', 'тощо', 'хоча', 'це', 'цей', 'чи', 'чого', 'що',
            'як', 'який', 'якої', 'які', 'їй', 'їм', 'їх', 'її', 'а', 'г', 'е', 'ж', 'з', 'м', 'т', 'у', 'я', 'є',
            'і', 'аж', 'за', 'зі', 'не', 'ну', 'нх', 'ні', 'по', 'то', 'ту', 'ті', 'цю', 'ця', 'ці', 'ще', 'або',
            'ало', 'ваш', 'вже', 'всю', 'вся', 'два', 'дві', 'ким', 'мож', 'моя', 'моє', 'мої', 'міг', 'між', 'мій',
            'над', 'нас', 'наш', 'нею', 'неї', 'них', 'ніж', 'ній', 'ось', 'при', 'пір', 'раз', 'рік', 'сам', 'сих',
            'сім', 'там', 'теж', 'тим', 'тих', 'той', 'тою', 'три', 'тут', 'хоч', 'хто', 'цим', 'цих', 'час', 'щоб',
            'яких', 'якщо', 'ім\'я', 'інша', 'інше', 'інші', 'буває', 'буде', 'буду', 'будь', 'вами', 'ваша', 'ваше',
            'ваші', 'вгору', 'вміти', 'вісім', 'давно', 'даром', 'добре', 'довго', 'друго', 'дякую', 'життя', 'зараз',
            'знову', 'какая', 'кожен', 'кожна', 'кожне', 'кожні', 'краще', 'менше', 'могти', 'можна', 'назад', 'немає',
            'нижче', 'нього', 'однак', 'п\'ять', 'перед', 'поруч', 'потім', 'проти', 'після', 'років', 'році', 'сама',
            'саме', 'саму', 'самі', 'свою', 'своє', 'свої', 'себе', 'собі', 'став', 'суть', 'така', 'таке', 'такі',
            'твоя', 'твоє', 'твій', 'тебе', 'тими', 'тобі', 'того', 'тоді', 'тому', 'туди', 'хіба', 'цими', 'цієї',
            'часу', 'чому', 'якого', 'іноді', 'інший', 'інших', 'багато', 'будемо', 'будете', 'будуть', 'більше',
            'всього', 'всьому', 'далеко', 'десять', 'досить', 'другий', 'дійсно', 'завжди', 'звідси', 'зовсім',
            'кругом', 'кілька', 'людина', 'можуть', 'навіть', 'навіщо', 'нагорі', 'небудь', 'низько', 'ніколи',
            'нікуди', 'нічого', 'обидва', 'одного', 'однієї', 'п\'ятий', 'перший', 'просто', 'раніше', 'раптом',
            'самим', 'самих', 'самій', 'свого', 'своєї', 'своїх', 'собою', 'справ', 'сказав', 'скрізь', 'сьомий',
            'третій', 'тільки', 'хотіти', 'чотири', 'чудово', 'шостий', 'близько', 'важлива', 'важливе', 'важливі',
            'вдалині', 'восьмий', 'говорив', 'дев\'ять', 'десятий', 'зайнята', 'зайнято', 'зайняті', 'занадто',
            'значить', 'навколо', 'нарешті', 'нерідко', 'повинно', 'посеред', 'початку', 'пізніше', 'сказала',
            'сказати', 'скільки', 'спасибі', 'частіше', 'важливий', 'двадцять', 'дев\'ятий', 'зазвичай', 'зайнятий',
            'звичайно', 'здається', 'найбільш', 'не можна', 'недалеко', 'особливо', 'потрібно', 'спочатку', 'сьогодні',
            'численна', 'численне', 'численні', 'відсотків', 'двадцятий', 'звідусіль', 'мільйонів', 'нещодавно',
            'прекрасно', 'четвертий', 'численний', 'будь ласка', 'дванадцять', 'одинадцять', 'сімнадцять',
            'тринадцять', 'безперервно', 'дванадцятий', 'одинадцятий', 'одного разу', 'п\'ятнадцять', 'сімнадцятий',
            'тринадцятий', 'шістнадцять', 'вісімнадцять', 'п\'ятнадцятий', 'чотирнадцять', 'шістнадцятий',
            'вісімнадцятий', 'дев\'ятнадцять', 'чотирнадцятий', 'дев\'ятнадцятий'
        }

        words = re.findall(r'\b\w+\b', query.lower())
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]

        candidates = []
        for n in range(1, 4):
            for i in range(len(filtered_words) - n + 1):
                candidate = ' '.join(filtered_words[i:i + n])
                candidates.append(candidate)

        candidates = list(set(candidates))

        if not candidates:
            return []

        pairs = [(query, cand) for cand in candidates]
        scores = self.cross_encoder.predict(pairs)

        scored_candidates = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

        if scored_candidates:
            max_score = scored_candidates[0][1]
            key_terms = [cand for cand, score in scored_candidates if
                         score >= max_score * 0.15] # Динамічне визначення top-k ключових термінів
        else:
            key_terms = []

        return key_terms

    def retrieve(
            self,
            query: str,
            filter_dict: Optional[Dict] = None,
            return_scores: bool = False
    ) -> List[Document] | List[RetrievalResult]:
        """
        Головний метод інформаційного пошуку

        Етапи інформаційного пошуку
        1. Гібридний пошук з EnsembleRetriever (розріджений BM25-пошук і щільний векторний пошук)
        2. LLM compression
        3. Cross-encoder re-ranking
        """
        if not self.ensemble_retriever:
            return []

        search_kwargs = {"k": self.top_k * 2}
        if filter_dict:
            search_kwargs["filter"] = filter_dict

        if self.use_llm_compression and self.compression_retriever:
            results = self.compression_retriever.invoke(query, **search_kwargs)
        else:
            results = self.ensemble_retriever.invoke(query, **search_kwargs)

        # Re-ranking за допомогою крос-енкодера
        reranked = self._cross_encoder_rerank(query, results)

        if return_scores:
            retrieval_results = []
            for i, (doc, score) in enumerate(reranked[:self.rerank_top_k]):
                retrieval_results.append(RetrievalResult(
                    document=doc,
                    relevance_score=score,
                    rank=i + 1
                ))
            return retrieval_results
        else:
            return [doc for doc, _ in reranked[:self.rerank_top_k]]
