# -*- coding: utf-8 -*-
import sys
import locale
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# Настройка кодировки для среды выполнения
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

# Для Windows-окружения
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def classify_email(message: str) -> str:
    """
    Классифицирует email-сообщение на важное, среднее или минимальное
    на основе его содержания.
    
    Args:
        message (str): Текст email-сообщения
        
    Returns:
        str: Категория сообщения (важное/среднее/минимальное)
    """
    # Инициализация модели через Groq
    chat = ChatOpenAI(
        model="llama3-70b-8192",
        base_url="https://api.groq.com/openai/v1",
        api_key="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",
        temperature=0.3
    )
    
    # Шаблон промпта для классификации
    prompt = ChatPromptTemplate.from_template(
        """Проанализируйте следующий текст email и определите, к какой категории он относится:
        - 'важное': если сообщение содержит срочные вопросы, дедлайны, финансовые вопросы, важные встречи
        - 'среднее': если сообщение содержит обычную рабочую переписку, обсуждения без срочности
        - 'минимальное': если это спам, рассылки, неперсонализированные сообщения или не требующие ответа
        
        Текст сообщения: {message}
        
        Ответьте только одним словом: 'важное', 'среднее' или 'минимальное'."""
    )
    
    # Создаем цепочку обработки
    chain = prompt | chat | StrOutputParser()
    
    # Получаем и обрабатываем ответ
    response = chain.invoke({"message": message}).strip().lower()
    
    if "важное" in response:
        return "важное"
    elif "среднее" in response:
        return "среднее"
    elif "минимальное" in response:
        return "минимальное"
    else:
        return "среднее"  # Значение по умолчанию

# Тестирование функции
if __name__ == "__main__":
    test_messages = [
        "Срочно! Проект должен быть сдан к завтрашнему дню, иначе мы потеряем клиента.",
        "Привет, как твои выходные? Хотел обсудить идею для нового проекта.",
        "Акция только сегодня! Скидка 50% на все курсы по программированию.",
        "Зоопарк приглашает на выставку экзотических животных!",
        "Ваш заказ №09090099 готов к выдаче. Сумма к оплате: 9000 руб."
    ]
    
    for index, msg in enumerate(test_messages, 1):
        try:
            category = classify_email(msg)
            print(f"Тест {index}:")
            print(f"Сообщение: {msg}")
            print(f"Категория: {category}\n")
        except Exception as e:
            print(f"Ошибка при обработке сообщения: {str(e)}")