import os
import re
from datetime import datetime
from typing import List, Dict, Optional

from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize bot and dispatcher
bot = Bot(token=('7646882683:AAF2DvdkSx7Fgn8gndjZWFpw8x8VUDnWFhk'))
dp = Dispatcher()

# Mock data storage for emails (in a real app, you'd use a database)
user_emails = {}
user_auth = {}

# States
class AuthState(StatesGroup):
    waiting_for_url = State()

class DateRangeState(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()

class SenderState(StatesGroup):
    waiting_for_sender = State()

class EmailSelectionState(StatesGroup):
    waiting_for_email_selection = State()

class SummaryState(StatesGroup):
    waiting_for_email_to_summarize = State()

class ImportanceState(StatesGroup):
    waiting_for_importance_level = State()

class TemplateState(StatesGroup):
    waiting_for_email_to_template = State()
    waiting_for_template_text = State()

# Helper functions
def create_email_list_keyboard(emails: List[Dict], page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Add email selection buttons
    for i, email in enumerate(emails[page*page_size:(page+1)*page_size], start=page*page_size):
        builder.add(InlineKeyboardButton(
            text=f"{i+1}. {email['subject']}",
            callback_data=f"select_email_{i}"
        ))
    
    # Add pagination if needed
    if len(emails) > page_size:
        row = []
        if page > 0:
            row.append(InlineKeyboardButton(
                text="⬅️ Previous",
                callback_data=f"email_page_{page-1}"
            ))
        if (page+1)*page_size < len(emails):
            row.append(InlineKeyboardButton(
                text="Next ➡️",
                callback_data=f"email_page_{page+1}"
            ))
        builder.row(*row)
    
    return builder.as_markup()

def get_main_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📅 Получить письма по дате")],
        [KeyboardButton(text="👤 Письма от отправителя")],
        [KeyboardButton(text="📝 Суммаризировать письмо")],
        [KeyboardButton(text="❗ Письма по важности")],
        [KeyboardButton(text="✉️ Написать шаблон ответа")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Handlers
@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "Здравствуйте! Это бот-секретарь. В этом боте вы можете:\n"
        "- Работать со своей почтой\n"
        "- Читать письма и быстро отвечать на них\n"
        "- Использовать ИИ для распределения писем по важности\n"
        "- Получать краткое содержание писем\n\n"
        "Для начала работы необходимо авторизоваться."
    )
    
    auth_button = InlineKeyboardButton(
        text="🔑 Авторизоваться",
        url="https://example.com/auth"  # Replace with your actual auth URL
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[auth_button]])
    
    instructions = (
        "Инструкция по авторизации:\n"
        "1. Нажмите на кнопку 'Авторизоваться'\n"
        "2. Перейдите на сайт для авторизации\n"
        "3. После авторизации скопируйте URL из адресной строки\n"
        "4. Отправьте этот URL в этот чат"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard)
    await message.answer(instructions)
    await message.answer("После авторизации вы получите доступ к функциям бота.")

@dp.message(F.text.contains("http") & AuthState.waiting_for_url)
async def process_auth_url(message: Message, state: FSMContext):
    # Here you would normally process the auth URL and verify it
    # For this example, we'll just assume it's valid
    
    user_auth[message.from_user.id] = {
        "auth_token": "mock_token",
        "email": "user@example.com"
    }
    
    await message.answer("✅ Авторизация прошла успешно!")
    await message.answer("Теперь вы можете использовать все функции бота.", reply_markup=get_main_keyboard())
    await state.clear()

# Date range emails
@dp.message(F.text == "📅 Получить письма по дате")
async def request_date_range(message: Message, state: FSMContext):
    if message.from_user.id not in user_auth:
        await message.answer("Пожалуйста, сначала авторизуйтесь.")
        return
    
    await message.answer("Введите начальную дату в формате ДД.ММ.ГГГГ:")
    await state.set_state(DateRangeState.waiting_for_start_date)

@dp.message(DateRangeState.waiting_for_start_date)
async def process_start_date(message: Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text, "%d.%m.%Y")
        await state.update_data(start_date=start_date)
        await message.answer("Введите конечную дату в формате ДД.ММ.ГГГГ:")
        await state.set_state(DateRangeState.waiting_for_end_date)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:")

@dp.message(DateRangeState.waiting_for_end_date)
async def process_end_date(message: Message, state: FSMContext):
    try:
        end_date = datetime.strptime(message.text, "%d.%m.%Y")
        data = await state.get_data()
        start_date = data['start_date']
        
        # Here you would normally fetch emails from your email service
        # For this example, we'll use mock data
        mock_emails = [
            {"id": i, "subject": f"Письмо {i}", "sender": "sender@example.com", "date": start_date, "content": f"Содержание письма {i}"}
            for i in range(1, 11)
        ]
        
        user_emails[message.from_user.id] = mock_emails
        
        if not mock_emails:
            await message.answer("Писем за указанный период не найдено.", reply_markup=get_main_keyboard())
            await state.clear()
            return
        
        await message.answer("Выберите письмо для просмотра:", reply_markup=create_email_list_keyboard(mock_emails))
        await state.set_state(EmailSelectionState.waiting_for_email_selection)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:")

# Sender emails
@dp.message(F.text == "👤 Письма от отправителя")
async def request_sender(message: Message, state: FSMContext):
    if message.from_user.id not in user_auth:
        await message.answer("Пожалуйста, сначала авторизуйтесь.")
        return
    
    await message.answer("Введите email отправителя:")
    await state.set_state(SenderState.waiting_for_sender)

@dp.message(SenderState.waiting_for_sender)
async def process_sender(message: Message, state: FSMContext):
    sender_email = message.text.strip()
    
    # Here you would normally fetch emails from your email service
    # For this example, we'll use mock data
    mock_emails = [
        {"id": i, "subject": f"Письмо от {sender_email} {i}", "sender": sender_email, "date": datetime.now(), "content": f"Содержание письма {i}"}
        for i in range(1, 6)
    ] if sender_email == "known@example.com" else []
    
    if not mock_emails:
        await message.answer(f"Писем от отправителя {sender_email} не найдено. Попробуйте ввести другой email.")
        return
    
    user_emails[message.from_user.id] = mock_emails
    await message.answer("Выберите письмо для просмотра:", reply_markup=create_email_list_keyboard(mock_emails))
    await state.set_state(EmailSelectionState.waiting_for_email_selection)

# Email summary
@dp.message(F.text == "📝 Суммаризировать письмо")
async def request_email_to_summarize(message: Message, state: FSMContext):
    if message.from_user.id not in user_auth:
        await message.answer("Пожалуйста, сначала авторизуйтесь.")
        return
    
    # Here you would normally fetch emails from your email service
    # For this example, we'll use mock data
    mock_emails = [
        {"id": i, "subject": f"Письмо для суммаризации {i}", "sender": "sender@example.com", "date": datetime.now(), "content": f"Это длинное содержание письма {i}, которое нужно сократить до основных моментов."}
        for i in range(1, 6)
    ]
    
    user_emails[message.from_user.id] = mock_emails
    await message.answer("Выберите письмо для суммаризации:", reply_markup=create_email_list_keyboard(mock_emails))
    await state.set_state(SummaryState.waiting_for_email_to_summarize)

@dp.callback_query(SummaryState.waiting_for_email_to_summarize, F.data.startswith("select_email_"))
async def summarize_email(callback: types.CallbackQuery, state: FSMContext):
    email_index = int(callback.data.split("_")[-1])
    emails = user_emails.get(callback.from_user.id, [])
    
    if not emails or email_index >= len(emails):
        await callback.answer("Письмо не найдено.")
        return
    
    selected_email = emails[email_index]
    
    # Here you would normally call your summarization AI
    summary = f"Краткое содержание письма '{selected_email['subject']}':\n\nОсновные моменты:\n1. Первый важный момент\n2. Второй важный момент\n3. Третий важный момент"
    
    await callback.message.answer(summary, reply_markup=get_main_keyboard())
    await state.clear()
    await callback.answer()

# Importance filter
@dp.message(F.text == "❗ Письма по важности")
async def request_importance_level(message: Message, state: FSMContext):
    if message.from_user.id not in user_auth:
        await message.answer("Пожалуйста, сначала авторизуйтесь.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Важное", callback_data="importance_high")],
        [InlineKeyboardButton(text="🟡 Среднее", callback_data="importance_medium")],
        [InlineKeyboardButton(text="🔵 Минимальная", callback_data="importance_low")]
    ])
    
    await message.answer("Выберите уровень важности:", reply_markup=keyboard)
    await state.set_state(ImportanceState.waiting_for_importance_level)

@dp.callback_query(ImportanceState.waiting_for_importance_level, F.data.startswith("importance_"))
async def show_emails_by_importance(callback: types.CallbackQuery, state: FSMContext):
    importance = callback.data.split("_")[-1]
    
    # Here you would normally fetch emails from your email service filtered by importance
    # For this example, we'll use mock data
    mock_emails = [
        {"id": i, "subject": f"{importance.capitalize()} важность письмо {i}", "sender": "sender@example.com", "date": datetime.now(), "content": f"Содержание {importance} важности письма {i}"}
        for i in range(1, 6)
    ]
    
    user_emails[callback.from_user.id] = mock_emails
    await callback.message.answer("Выберите письмо для просмотра:", reply_markup=create_email_list_keyboard(mock_emails))
    await state.set_state(EmailSelectionState.waiting_for_email_selection)
    await callback.answer()

# Response template
@dp.message(F.text == "✉️ Написать шаблон ответа")
async def request_email_for_template(message: Message, state: FSMContext):
    if message.from_user.id not in user_auth:
        await message.answer("Пожалуйста, сначала авторизуйтесь.")
        return
    
    # Here you would normally fetch emails from your email service
    # For this example, we'll use mock data
    mock_emails = [
        {"id": i, "subject": f"Письмо для шаблона ответа {i}", "sender": "sender@example.com", "date": datetime.now(), "content": f"Оригинальное содержание письма {i}"}
        for i in range(1, 6)
    ]
    
    user_emails[message.from_user.id] = mock_emails
    await message.answer("Выберите письмо для создания шаблона ответа:", reply_markup=create_email_list_keyboard(mock_emails))
    await state.set_state(TemplateState.waiting_for_email_to_template)

@dp.callback_query(TemplateState.waiting_for_email_to_template, F.data.startswith("select_email_"))
async def create_response_template(callback: types.CallbackQuery, state: FSMContext):
    email_index = int(callback.data.split("_")[-1])
    emails = user_emails.get(callback.from_user.id, [])
    
    if not emails or email_index >= len(emails):
        await callback.answer("Письмо не найдено.")
        return
    
    selected_email = emails[email_index]
    await state.update_data(selected_email=selected_email)
    
    await callback.message.answer(
        f"Создание шаблона ответа на письмо: '{selected_email['subject']}'\n\n"
        "Пожалуйста, введите текст шаблона ответа:"
    )
    await state.set_state(TemplateState.waiting_for_template_text)
    await callback.answer()

@dp.message(TemplateState.waiting_for_template_text)
async def save_response_template(message: Message, state: FSMContext):
    data = await state.get_data()
    selected_email = data['selected_email']
    
    # Here you would normally save the template
    template_text = message.text
    
    await message.answer(
        f"Шаблон ответа для письма '{selected_email['subject']}' сохранен:\n\n"
        f"{template_text}",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# Email selection handler (shared for multiple states)
@dp.callback_query(EmailSelectionState.waiting_for_email_selection, F.data.startswith("select_email_"))
async def show_selected_email(callback: types.CallbackQuery, state: FSMContext):
    email_index = int(callback.data.split("_")[-1])
    emails = user_emails.get(callback.from_user.id, [])
    
    if not emails or email_index >= len(emails):
        await callback.answer("Письмо не найдено.")
        return
    
    selected_email = emails[email_index]
    
    email_text = (
        f"От: {selected_email['sender']}\n"
        f"Дата: {selected_email['date'].strftime('%d.%m.%Y %H:%M')}\n"
        f"Тема: {selected_email['subject']}\n\n"
        f"Содержание:\n{selected_email['content']}"
    )
    
    await callback.message.answer(email_text, reply_markup=get_main_keyboard())
    await state.clear()
    await callback.answer()

# Pagination handler
@dp.callback_query(F.data.startswith("email_page_"))
async def handle_email_pagination(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    emails = user_emails.get(callback.from_user.id, [])
    
    if not emails:
        await callback.answer("Письма не найдены.")
        return
    
    await callback.message.edit_reply_markup(reply_markup=create_email_list_keyboard(emails, page))
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())