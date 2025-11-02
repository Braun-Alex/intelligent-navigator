import re
from typing import List, Optional, Dict
from langchain_text_splitters import TextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from dataclasses import dataclass


@dataclass
class DocumentSection:
    """Ієрархічний розділ документа"""
    level: int
    number: str
    title: str
    content: str
    parent: Optional[str] = None


class LegalDocumentChunker(TextSplitter):
    """
    Розбиває українські нормативні документи КНУТШ на чанки з урахуванням

    1) Нормативної структури
    2) Речень (з використанням spaCy для української мови)
    3) Розміру з накладанням
    4) Контексту (заголовок розділу додається до кожного чанку)
    5) Дедублікації: видаляє майже ідентичні чанки (через накладання)
    """

    def __init__(
        self,
        embeddings: Embeddings,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        length_function: callable = len,
        min_chunk_size: int = 50,
        embedding_batch_size: int = 128
    ):
        self.embeddings = embeddings
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.min_chunk_size = min_chunk_size
        self.embedding_batch_size = embedding_batch_size

        # Завантаження моделі spaCy для української мови
        self.nlp = spacy.load("uk_core_news_sm")

        # Регулярні вирази для структури нормативного документа
        self.section_patterns = {
            'chapter': re.compile(r'(Розділ|Глава)\s+([IVX\d]+)[\.\s]*(.+?)(?=\n|$)', re.IGNORECASE | re.UNICODE),
            'article': re.compile(r'(Стаття)\s+(\d+)[\.\s]*(.+?)(?=\n|$)', re.IGNORECASE | re.UNICODE),
            'section': re.compile(r'(Частина)\s+(\d+)[\.\s]*(.+?)(?=\n|$)', re.IGNORECASE | re.UNICODE),
            'point': re.compile(r'(Пункт)\s+(\d+)[\.\s]*(.+?)(?=\n|$)', re.IGNORECASE | re.UNICODE),
            'subsection': re.compile(r'(\d+)\.(\d+)\.(\d+)\.?\s+(.+?)(?=\n|$)', re.UNICODE),
            'numbered_list': re.compile(r'^[\s]*(\d+[.\)])\s+(.+?)(?=\n|$)', re.MULTILINE | re.UNICODE),
            'list_item': re.compile(r'^[\s]*[-•◦*➢✔✘]\s+(.+?)(?=\n|$)', re.MULTILINE | re.UNICODE),
        }

    def split_text(self, text: str) -> List[str]:
        """Розбиває текст на чанки"""
        sections = self._identify_sections(text)
        chunks = []

        for section in sections:
            section_chunks = self._chunk_section(section)
            chunks.extend(section_chunks)

        chunks = self._deduplicate_chunks(chunks)

        return chunks

    def _identify_sections(self, text: str) -> List[DocumentSection]:
        """Визначає ієрархічні розділи"""
        sections = []
        lines = text.split('\n')
        current_section = None
        current_level = 0
        current_content = []
        parent_stack = []

        for line in lines:
            stripped = line.strip()
            matched = False

            for level, (name, pattern) in enumerate(self.section_patterns.items(), 1):
                match = pattern.match(stripped)
                if match:
                    if current_section:
                        current_section.content = '\n'.join(current_content).strip()
                        sections.append(current_section)

                    # Виконуємо екстракцію номера і заголовка
                    number, title = self._extract_number_title(name, match)

                    parent = parent_stack[-1].number if parent_stack and level > current_level else None

                    current_section = DocumentSection(
                        level=level,
                        number=number,
                        title=title.strip(),
                        content="",
                        parent=parent
                    )

                    if level > current_level:
                        parent_stack.append(current_section)
                    elif level < current_level:
                        parent_stack = parent_stack[:level - 1]
                    current_level = level

                    current_content = [line]
                    matched = True
                    break

            if not matched and current_section:
                current_content.append(line)

        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)

        if not sections:
            sections.append(DocumentSection(level=0, number="0", title="Повний документ", content=text.strip()))

        return sections

    def _extract_number_title(self, name: str, match) -> tuple[str, str]:
        """Допоміжна функція для екстракції номера і заголовка"""
        if name in ['chapter', 'article', 'section', 'point']:
            number = match.group(2) if len(match.groups()) >= 2 else ''
            title = match.group(3) if len(match.groups()) >= 3 else ''
        elif name == 'subsection':
            parts = [match.group(i) for i in range(1, 4) if match.group(i)]
            number = '.'.join(parts)
            title = match.group(4) if len(match.groups()) >= 4 else ''
        elif name == 'numbered_list':
            number = match.group(1)
            title = match.group(2) if len(match.groups()) >= 2 else ''
        elif name == 'list_item':
            number = ''
            title = match.group(1)
        else:
            number = ''
            title = ''
        return number, title

    def _chunk_section(self, section: DocumentSection) -> List[str]:
        """Розбиває один розділ на чанки"""
        content = section.content.strip()
        if not content or len(content) < self.min_chunk_size:
            return []

        doc = self.nlp(content)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

        if not sentences:
            return []

        chunks = []
        current_sentences = []
        current_length = 0
        header = f"{section.number}. {section.title}\n\n" if section.title else ""
        header_len = len(header)

        for sentence in sentences:
            sent_len = len(sentence) + 1

            # Якщо перевищуємо розмір — фіналізуємо чанк
            if current_length + sent_len + header_len > self.chunk_size and current_sentences:
                chunk_text = header + ' '.join(current_sentences)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(chunk_text)

                # Накладання: беремо останні речення до chunk_overlap
                overlap_sentences = self._get_overlap(current_sentences)
                current_sentences = overlap_sentences
                current_length = sum(len(s) + 1 for s in overlap_sentences)

            current_sentences.append(sentence)
            current_length += sent_len

        # Останній чанк
        if current_sentences:
            chunk_text = header + ' '.join(current_sentences)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)

        return chunks

    def _get_overlap(self, sentences: List[str]) -> List[str]:
        """Повертає останні речення, що вписуються в chunk_overlap"""
        if not sentences:
            return []

        overlap = []
        length = 0
        for sent in reversed(sentences):
            if length + len(sent) + 1 > self.chunk_overlap:
                break
            overlap.insert(0, sent)
            length += len(sent) + 1
        return overlap or [sentences[-1]]

    def _deduplicate_chunks(self, chunks: List[str]) -> List[str]:
        """Видаляє майже ідентичні чанки (через накладання)"""
        if len(chunks) < 2:
            return chunks

        embeddings = []
        for i in range(0, len(chunks), self.embedding_batch_size):
            batch = chunks[i:i + self.embedding_batch_size]
            batch_emb = self.embeddings.embed_documents(batch)
            embeddings.extend(batch_emb)

        filtered = [chunks[0]]
        last_emb = embeddings[0]

        for chunk, emb in zip(chunks[1:], embeddings[1:]):
            sim = cosine_similarity([last_emb], [emb])[0][0]
            if sim < 0.9: # Поріг подібності
                filtered.append(chunk)
                last_emb = emb

        return filtered

    def create_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None
    ) -> List[Document]:
        """Створює LangChain Document з метаданими"""
        _metadatas = metadatas or [{} for _ in texts]
        docs = []

        for i, text in enumerate(texts):
            meta = _metadatas[i].copy()

            # Виконуємо екстракцію номера і назви розділу з чанку
            header_match = re.match(r'^(\d+(?:\.\d+)*)\.\s+(.+?)\n\n', text)
            if header_match:
                meta['section_number'] = header_match.group(1)
                meta['section_title'] = header_match.group(2).strip()

            meta.update({
                'chunk_length': len(text),
                'chunk_index': i,
                'splitting_method': 'legal_hierarchical'
            })

            docs.append(Document(page_content=text, metadata=meta))

        return docs


class HybridLegalDocumentSplitter:
    def __init__(
        self,
        embeddings: Embeddings,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        embedding_batch_size: int = 128
    ):
        self.chunker = LegalDocumentChunker(
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
        all_chunks = []
        for doc in documents:
            try:
                texts = self.chunker.split_text(doc.page_content)
                chunk_docs = self.chunker.create_documents(texts, [doc.metadata] * len(texts))
                all_chunks.extend(chunk_docs)
            except Exception as error:
                print(f"Гібридне розбиття не вдалося для {doc.metadata.get('source')}: {error}. Використовуємо рекурсивне розбиття...")
                fallback_docs = self.fallback.split_documents([doc])
                for i, d in enumerate(fallback_docs):
                    d.metadata['chunk_index'] = i
                    d.metadata['splitting_method'] = 'recursive_fallback'
                all_chunks.extend(fallback_docs)
        return all_chunks
