from dataclasses import dataclass
from typing import Optional, Set
from langchain_core.language_models import BaseLLM

from app.rag.prompts.prompt_templates import ethics_check_prompt, relevance_check_prompt


@dataclass
class QueryValidationResult:
    """Результат валідації запиту"""
    is_valid: bool
    is_relevant: bool
    is_ethical: bool
    rejection_reason: Optional[str] = None


class QueryValidator:
    """
    Валідація запитів
    
    Перевірки:
    1. Етичність запиту
    2. Релевантність до документів КНУТШ
    3. Фільтрація за ключовими словами
    """
    
    def __init__(self, llm: BaseLLM, use_llm_validation: bool = True):
        self.llm = llm
        self.use_llm_validation = use_llm_validation
        
        # Ключові слова для fallback-перевірки
        self.knu_keywords = {
            'кну', 'шевченк', 'університет', 'студент', 'викладач', 'екзамен', 'іспит', 'академічн', 'навчальн',
            'освітн', 'атестаці', 'залік', 'курс', 'доброчесн', 'положен', 'регламент', 'документ', 'норматив',
            'семестр', 'оцінк', 'диплом', 'відрахув', 'переведен', 'стипенді', 'вступ', 'захист', 'науков',
            'бібліотек', 'самоврядуван',  'додатков курс', 'правила поведінк', 'ініціатив'
        }
        
        # Неетичні слова для швидкої перевірки
        self.unethical_keywords = {
            'політ', 'партія', 'вибор', 'еротик', 'порно', 'секс', 'насильств', 'вбивств', 'дискримінац', 'расизм',
            'фашизм', 'нацизм', 'нетерпим', 'суїцид', 'ненавист', 'шахрайств', 'реклам', 'спам', 'хакінг', 'злом',
            'фінансов схем', 'експлуатаці', 'фейков новин', 'шкідлив ПЗ', 'війн', 'дискримінац',
            'насильств над тваринами', 'тероризм', 'фальшив документ', 'плагіат', 'персональн дан', 'маніпуляц'
        }
    
    def validate_query(self, query: str) -> QueryValidationResult:
        """
        Валідація запиту
        """
        # Перевірка на порожній запит
        if not query or len(query.strip()) < 3:
            return QueryValidationResult(
                is_valid=False,
                is_relevant=False,
                is_ethical=True,
                rejection_reason="Запит занадто короткий. Будь ласка, сформулюйте питання більш детально."
            )
        
        query_lower = query.lower()
        
        # Швидка перевірка на неетичні слова
        if any(keyword in query_lower for keyword in self.unethical_keywords):
            return QueryValidationResult(
                is_valid=False,
                is_relevant=False,
                is_ethical=False,
                rejection_reason="Запит стосується неприйнятних тем. Система є призначеною лише для питань про нормативні документи КНУТШ."
            )
        
        if self.use_llm_validation:
            # Валідація запиту за допомогою LLM
            return self._llm_validate(query)
        else:
            # Fallback-валідація запиту за допомогою keyword-based валідації
            return self._keyword_validate(query)
    
    def _llm_validate(self, query: str) -> QueryValidationResult:
        """Валідація запиту за допомогою LLM"""
        
        # Перевірка запиту на етичність
        try:
            ethics_prompt = ethics_check_prompt.format(query=query)
            ethics_response = self.llm.invoke(ethics_prompt).content.strip().upper()
            
            is_ethical = "ЕТИЧНИЙ" in ethics_response or "ETHICAL" in ethics_response
            
            if not is_ethical:
                return QueryValidationResult(
                    is_valid=False,
                    is_relevant=False,
                    is_ethical=False,
                    rejection_reason="Запит стосується неприйнятних тем для академічної системи. Будь ласка, сформулюйте питання, пов'язане з нормативними документами КНУТШ."
                )
        except Exception as error:
            print(f"Помилка при перевірці запиту на етичність за допомогою LLM: {error}")
            # Fallback-перевірка запиту на етичність
            if any(keyword in query.lower() for keyword in self.unethical_keywords):
                return QueryValidationResult(
                    is_valid=False,
                    is_relevant=False,
                    is_ethical=False,
                    rejection_reason="Запит стосується неприйнятних тем. Система є призначеною лише для питань про нормативні документи КНУТШ."
                )
        
        # Перевірка релевантності
        try:
            relevance_prompt = relevance_check_prompt.format(query=query)
            relevance_response = self.llm.invoke(relevance_prompt).content.strip().upper()
            
            is_relevant = "РЕЛЕВАНТНИЙ" in relevance_response or "RELEVANT" in relevance_response
            
            if not is_relevant:
                return QueryValidationResult(
                    is_valid=False,
                    is_relevant=False,
                    is_ethical=True,
                    rejection_reason="Ваш запит не стосується нормативних документів КНУТШ. Система є призначеною для пошуку інформації в університетських положеннях та регламентах. Будь ласка, сформулюйте питання про правила, процедури або вимоги КНУТШ."
                )
        except Exception as error:
            print(f"Помилка при перевірці запиту на релевантність за допомогою LLM: {error}")
            # Fallback-перевірка запиту на релевантність
            if not any(keyword in query.lower() for keyword in self.knu_keywords):
                return QueryValidationResult(
                    is_valid=False,
                    is_relevant=False,
                    is_ethical=True,
                    rejection_reason="Ваш запит не стосується нормативних документів КНУТШ. Будь ласка, сформулюйте питання про університетські положення та регламенти."
                )
        
        # Запит пройшов обидві перевірки
        return QueryValidationResult(
            is_valid=True,
            is_relevant=True,
            is_ethical=True
        )
    
    def _keyword_validate(self, query: str) -> QueryValidationResult:
        """
        Fallback-валідація на основі ключових слів
        """
        query_lower = query.lower()
        
        # Перевірка запиту на етичність
        is_ethical = not any(topic in query_lower for topic in self.unethical_keywords)
        
        if not is_ethical:
            return QueryValidationResult(
                is_valid=False,
                is_relevant=False,
                is_ethical=False,
                rejection_reason="Запит стосується неприйнятних тем. Система є призначеною лише для питань про нормативні документи КНУТШ."
            )
        
        # Перевірка запиту на релевантність
        is_relevant = any(keyword in query_lower for keyword in self.knu_keywords)
        
        if not is_relevant:
            return QueryValidationResult(
                is_valid=False,
                is_relevant=False,
                is_ethical=True,
                rejection_reason="Ваш запит не стосується нормативних документів КНУТШ. Будь ласка, сформулюйте питання про університетські положення та регламенти."
            )
        
        return QueryValidationResult(
            is_valid=True,
            is_relevant=True,
            is_ethical=True
        )
