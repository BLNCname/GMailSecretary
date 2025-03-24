# -*- coding: utf-8 -*-
import sys
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from configs.configs import GROQ_API_KEY

# Установка кодировки для вывода
sys.stdout.reconfigure(encoding='utf-8')

# Инициализация модели через Groq
# Используем модель "llama3-70b-8192", которая должна быть доступна в Groq
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="llama3-70b-8192",  # Проверяем точное название модели
    temperature=0.1,
    max_tokens=100
)

# Создание шаблона промпта для суммаризации
summarize_template = """
Ты — суммаризатор. Создай краткое резюме на русском, сохранив только ключевую информацию в максимум 50 слов из текста: {text}
"""

summarize_prompt = ChatPromptTemplate.from_template(summarize_template)

# Создание цепочки для суммаризации с использованием LCEL
summarize_chain = summarize_prompt | llm | StrOutputParser()

def summarize_text(text):
    """
    Функция для суммаризации текста
    
    Args:
        text (str): Исходный текст для суммаризации
        
    Returns:
        str: Суммаризированный текст
    """
    summary = summarize_chain.invoke({"text": text})
    return summary.strip()

# Пример использования
if __name__ == "__main__":
    # Пример текста для суммаризации
    sample_text = "ДОБРЫЙ ДЕНЬ, УВАЖАЕМЫЙ ИВАН ИВАНОВИЧ! НАДЕЕМСЯ, ЧТО У ВАС ВСЕ ХОРОШО, И ВЫ ПРОВОДИТЕ ЭТОТ ДЕНЬ С УДОВОЛЬСТВИЕМ. МЫ РАДЫ СООБЩИТЬ ВАМ, ЧТО ВАША ЗАРПЛАТА ЗА АВГУСТ 2024 ГОДА, КОТОРАЯ БЫЛА НАЧИСЛЕНА В СООТВЕТСТВИИ С ВАШИМ ТРУДОВЫМ ДОГОВОРОМ И УЧЕТОМ ВСЕХ НАЛОГОВ, УСПЕШНО ПЕРЕВЕДЕНА НА ВАШ БАНКОВСКИЙ СЧЕТ. СУММА СОСТАВЛЯЕТ 75 000 РУБЛЕЙ, ЧТО, КАК МЫ ПОНИМАЕМ, ЯВЛЯЕТСЯ ДЛЯ ВАС ВАЖНОЙ ИНФОРМАЦИЕЙ. ВСЕ ДЕТАЛИ ВЫ МОЖЕТЕ УВИДЕТЬ В ВАШЕМ ЛИЧНОМ КАБИНЕТЕ, ГДЕ ТАКЖЕ ДОСТУПНА ИСТОРИЯ ВСЕХ ОПЕРАЦИЙ. ЕСЛИ ВОЗНИКНУТ КАКИЕ-ЛИБО ВОПРОСЫ, МЫ ВСЕГДА РАДЫ ПОМОЧЬ. С УВАЖЕНИЕМ, БУХГАЛТЕРИЯ ООО 'РОМАШКА'."
    
    # Получение суммаризации
    summary = summarize_text(sample_text)
    print("Исходный текст:")
    print(sample_text)
    print("\nСуммаризация:")
    print(summary)
