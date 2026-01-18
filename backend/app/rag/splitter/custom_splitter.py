from typing import List
from langchain_text_splitters import TextSplitter
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import spacy
from sklearn.metrics.pairwise import cosine_similarity


class DocumentSplitter(TextSplitter):
    """
    Розбиває українські нормативні документи КНУТШ на чанки з урахуванням

    1) Речень (з використанням spaCy для української мови)
    2) Накладання
    3) Дедублікації: видаляє майже ідентичні чанки (через накладання)
    """

    def __init__(
        self,
        embeddings: Embeddings,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        min_chunk_size: int = 50,
        embedding_batch_size: int = 128
    ):
        self.embeddings = embeddings
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.embedding_batch_size = embedding_batch_size

        # Завантаження spaCy моделі для української мови
        self.nlp = spacy.load("uk_core_news_sm")

    def split_text(self, text: str) -> List[str]:
        """Розбиває текст на чанки з урахуванням речень"""
        if not text or len(text) < self.min_chunk_size:
            return []

        # Сегментація тексту на речення за допомогою spaCy
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

        if not sentences:
            return []

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sent_length = len(sentence) + 1 # Для пробілу

            # Якщо додавання речення перевищує розмір чанку, зберігаємо поточний чанк
            if current_length + sent_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(chunk_text)

                # Створюємо накладання: беремо останні речення до розміру накладання
                overlap_chunk = []
                overlap_length = 0
                for sent in reversed(current_chunk):
                    sent_len = len(sent) + 1
                    if overlap_length + sent_len > self.chunk_overlap:
                        break
                    overlap_chunk.insert(0, sent)
                    overlap_length += sent_len

                current_chunk = overlap_chunk if overlap_chunk else [current_chunk[-1]]
                current_length = sum(len(s) + 1 for s in current_chunk)

            current_chunk.append(sentence)
            current_length += sent_length

        # Додаємо останній чанк
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)

        # Дедуплікація через схожість вбудовувань
        chunks = self._deduplicate_chunks(chunks)

        return chunks

    def _deduplicate_chunks(self, chunks: List[str]) -> List[str]:
        """Видаляє дублікати чанків на основі косинусної схожості"""
        if len(chunks) < 2:
            return chunks

        # Генерація вбудовувань батчами
        embeddings = []
        for i in range(0, len(chunks), self.embedding_batch_size):
            batch = chunks[i:i + self.embedding_batch_size]
            batch_emb = self.embeddings.embed_documents(batch)
            embeddings.extend(batch_emb)

        # Фільтрація дублікатів
        filtered = [chunks[0]]
        last_emb = embeddings[0]

        for chunk, emb in zip(chunks[1:], embeddings[1:]):
            # Якщо схожість є меншою за 99%, залишаємо чанк
            sim = cosine_similarity([last_emb], [emb])[0][0]
            if sim < 0.99:
                filtered.append(chunk)
                last_emb = emb

        return filtered

    def create_documents(
        self,
        texts: List[str],
        metadatas: List[dict] = None
    ) -> List[Document]:
        """Створює LangChain Documents з метаданими"""
        _metadatas = metadatas or [{} for _ in texts]
        docs = []

        for i, text in enumerate(texts):
            meta = _metadatas[i].copy()
            meta.update({
                'chunk_length': len(text),
                'chunk_index': i,
                'splitting_method': 'simplified_spacy'
            })
            docs.append(Document(page_content=text, metadata=meta))

        return docs


class HybridLegalDocumentSplitter:
    """
    Гібридний розбивач з fallback-механізмом
    Спочатку намагається використати DocumentSplitter,
    якщо не вдається, то використовує RecursiveCharacterTextSplitter
    """

    def __init__(
        self,
        embeddings: Embeddings,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        embedding_batch_size: int = 128
    ):
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self.splitter = DocumentSplitter(
            embeddings=embeddings,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_batch_size=embedding_batch_size
        )

        self.fallback = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=True,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Розбиває документи на чанки"""
        all_chunks = []

        for doc in documents:
            try:
                # Розбиття за допомогою DocumentSplitter
                texts = self.splitter.split_text(doc.page_content)
                chunk_docs = self.splitter.create_documents(
                    texts,
                    [doc.metadata] * len(texts)
                )
                all_chunks.extend(chunk_docs)

            except Exception as error:
                # Fallback-механізм
                print(
                    f"Помилка при розбитті {doc.metadata.get('source')}: {error}. "
                    f"Використовується альтернативний механізм розбиття тексту..."
                )
                fallback_docs = self.fallback.split_documents([doc])
                for i, d in enumerate(fallback_docs):
                    d.metadata['chunk_index'] = i
                    d.metadata['splitting_method'] = 'recursive_fallback'
                all_chunks.extend(fallback_docs)

        return all_chunks
