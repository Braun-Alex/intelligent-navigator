from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from langchain_core.documents import Document
from langchain_core.language_models import BaseLLM
import re
import json
from datetime import datetime

from app.rag.prompts.prompt_templates import (
    faithfulness_evaluation_prompt,
    relevancy_evaluation_prompt,
    context_relevancy_prompt
)


@dataclass
class EvaluationMetrics:
    """Основні метрики для оцінки якості RAG-системи"""
    faithfulness: float
    answer_relevancy: float
    context_relevancy: float
    mrr: float # Mean Reciprocal Rank
    map_score: float # Mean Average Precision
    overall_score: float
    individual_relevancy: List[bool]
    timestamp: str
    query: str
    answer: str
    num_contexts: int


class RAGQualityEvaluator:
    """
    Система оцінки якості RAG-системи
    
    Метрики:
    1. Faithfulness - чи відповідь обґрунтовано контекстом
    2. Answer Relevancy - чи відповідь відповідає на запит
    3. Context Relevancy - чи контексти є релевантними
    4. MRR - Mean Reciprocal Rank
    5. MAP - Mean Average Precision
    """
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self.evaluation_history: List[EvaluationMetrics] = []
    
    def evaluate(
        self,
        query: str,
        answer: str,
        contexts: List[Document]
    ) -> EvaluationMetrics:
        """
        Оцінка якості відповіді RAG-системи
        
        Аргументи:
            query: запит користувача
            answer: згенерована відповідь
            contexts: отримані контексти
        
        Повертає об'єкт EvaluationMetrics з усіма оцінками якості відповіді
        """
        context_texts = [doc.page_content for doc in contexts]

        faithfulness = self._evaluate_faithfulness(answer, context_texts)
        answer_relevancy = self._evaluate_answer_relevancy(query, answer)
        individual_relevancy, context_relevancy = self._evaluate_context_relevancy(query, context_texts)

        mrr = self._calculate_mrr(context_texts, individual_relevancy)
        map_score = self._calculate_map(context_texts, individual_relevancy)

        overall_score = (
            faithfulness * 0.3 +
            answer_relevancy * 0.3 +
            context_relevancy * 0.1 +
            mrr * 0.15 +
            map_score * 0.15
        )
        
        metrics = EvaluationMetrics(
            faithfulness=faithfulness,
            answer_relevancy=answer_relevancy,
            context_relevancy=context_relevancy,
            mrr=mrr,
            map_score=map_score,
            overall_score=overall_score,
            individual_relevancy=individual_relevancy,
            timestamp=datetime.now().isoformat(),
            query=query,
            answer=answer,
            num_contexts=len(contexts)
        )
        
        self.evaluation_history.append(metrics)

        return metrics
    
    def _evaluate_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """Оцінка достовірності відповіді на основі отриманого контексту"""
        if not answer or not contexts:
            return 0.0

        combined_context = "\n\n".join(contexts)

        prompt = faithfulness_evaluation_prompt.format(
            context=combined_context,
            answer=answer
        )
        
        try:
            response = self.llm.invoke(prompt).content.strip()
            score = self._extract_score(response)
            return max(0.0, min(1.0, score))

        except Exception as error:
            print(f"Помилка при оцінці достовірності відповіді системи: {error}")

            return self._overlap_score(answer, combined_context)
    
    def _evaluate_answer_relevancy(self, query: str, answer: str) -> float:
        """Оцінка релевантності відповіді на запит інформаційного пошуку"""
        if not answer or not query:
            return 0.0
        
        prompt = relevancy_evaluation_prompt.format(
            query=query,
            answer=answer
        )
        
        try:
            response = self.llm.invoke(prompt).content.strip()
            score = self._extract_score(response)
            return max(0.0, min(1.0, score))

        except Exception as error:
            print(f"Помилка при оцінці релевантності відповіді на запит: {error}")
            return self._overlap_score(query, answer)

    def _evaluate_context_relevancy(self, query: str, contexts: List[str]) -> Tuple[List[bool], float]:
        """
        Оцінка релевантності отриманих контекстів на запит
        Виконується батч-оцінка: один LLM-запит використовується для оцінки всіх фрагментів окремо і загалом
        """
        if not contexts or not query:
            return [], 0.0

        # Підготовка батч-запиту
        batch_context = "\n\n".join([f"Контекст {i + 1}.\n{ctx}" for i, ctx in enumerate(contexts)])
        prompt = context_relevancy_prompt.format(
            query=query,
            context=batch_context
        )

        try:
            response = self.llm.invoke(prompt).content.strip()
            parsed = json.loads(response)
            individual_relevancy = parsed.get('individual_score', [False] * len(contexts))
            overall_relevancy = parsed.get('overall_score', 0.0)

            return individual_relevancy, max(0.0, min(1.0, overall_relevancy))

        except Exception as error:
            print(f"Помилка при оцінці релевантності отриманих контекстів: {error}")

            return sum(self._overlap_score(query, ctx) for ctx in contexts) / len(contexts)

    def _calculate_mrr(self, retrieved_docs: List[Document], individual_relevancy: List[bool]) -> float:
        """
        Обчислення Mean Reciprocal Rank
        """
        if len(individual_relevancy) != len(retrieved_docs):
            return 0.0

        for i, is_rel in enumerate(individual_relevancy, 1):
            if is_rel:
                return 1.0 / i
        return 0.0

    def _calculate_map(self, retrieved_docs: List[Document], individual_relevancy: List[bool]) -> float:
        """
        Обчислення Mean Average Precision
        """
        if len(individual_relevancy) != len(retrieved_docs):
            return 0.0

        total_relevant = sum(individual_relevancy)
        if total_relevant == 0:
            return 0.0

        relevant_count = 0
        precision_sum = 0.0
        for i, is_rel in enumerate(individual_relevancy, 1):
            if is_rel:
                relevant_count += 1
                precision_sum += relevant_count / i
        return precision_sum / total_relevant
    
    def _extract_score(self, text: str) -> float:
        """Отримання числової оцінки з тексту відповіді"""
        text = text.strip()

        # Шукаємо найбільш ймовірне число
        patterns = [
            r'(?:оцінка[:\s]*)?(\d?\.\d+)', # .85 або 0.85 після слова "оцінка"
            r'(?:оцінка[:\s]*)?(\d+\.\d+)', # 1.0, 0.5 тощо
            r'(?:оцінка[:\s]*)?(0|1)(?:\D|$)', # 0 або 1 окремо
            r'(\d?\.\d+)', # будь-яке число типу .85
            r'(\d+\.\d+)', # будь-яке число типу 0.85
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    # Перевіряємо що оцінка перебуває в межах проміжку [0, 1]
                    if 0 <= score <= 1:
                        return score
                except (ValueError, IndexError):
                    continue
        
        # Якщо відповіді містить відсотки
        match = re.search(r'(\d+)%', text)
        if match:
            try:
                return min(float(match.group(1)) / 100.0, 1.0)
            except ValueError:
                pass
        
        # Встановлюємо нульове значення, якщо не змогли розпізнати відповідь
        print(f"Попередження: не вдалося розпізнати оцінку в тексті: '{text[:100]}'")
        return 0.0
    
    def _overlap_score(self, text1: str, text2: str) -> float:
        """Оцінка перетину слів"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_evaluation_report(self) -> Dict[str, Any]:
        """Надання комплексного звіту оцінки якості системи на основі історії запитів з увімкненою оцінкою якості відповідей"""
        if not self.evaluation_history:
            return {
                "total_evaluations": 0,
                "average_metrics": {},
                "latest_evaluation": None,
                "trend": {"trend": "no_data"}
            }
        
        # Середні метрики
        avg_faithfulness = sum(e.faithfulness for e in self.evaluation_history) / len(self.evaluation_history)
        avg_answer_relevancy = sum(e.answer_relevancy for e in self.evaluation_history) / len(self.evaluation_history)
        avg_context_relevancy = sum(e.context_relevancy for e in self.evaluation_history) / len(self.evaluation_history)
        avg_mrr = sum(e.mrr for e in self.evaluation_history) / len(self.evaluation_history)
        avg_map = sum(e.map_score for e in self.evaluation_history) / len(self.evaluation_history)
        avg_overall = sum(e.overall_score for e in self.evaluation_history) / len(self.evaluation_history)
        
        # Тренд
        if len(self.evaluation_history) >= 3:
            recent_avg = sum(e.overall_score for e in self.evaluation_history[-3:]) / 3
            older_avg = sum(e.overall_score for e in self.evaluation_history[:3]) / 3
            
            if recent_avg > older_avg + 0.05:
                trend = "improving"
            elif recent_avg < older_avg - 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        latest = self.evaluation_history[-1]
        
        return {
            "total_evaluations": len(self.evaluation_history),
            "average_metrics": {
                "avg_faithfulness": avg_faithfulness,
                "avg_answer_relevancy": avg_answer_relevancy,
                "avg_relevancy": avg_context_relevancy,
                "avg_mrr": avg_mrr,
                "avg_map": avg_map,
                "avg_overall_score": avg_overall
            },
            "latest_evaluation": {
                "query": latest.query,
                "answer": latest.answer,
                "faithfulness": latest.faithfulness,
                "answer_relevancy": latest.answer_relevancy,
                "relevancy": latest.context_relevancy,
                "mrr": latest.mrr,
                "map_score": latest.map_score,
                "overall_score": latest.overall_score,
                "timestamp": latest.timestamp
            },
            "trend": {"trend": trend}
        }
