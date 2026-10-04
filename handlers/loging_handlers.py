from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from keyboards.keyboards import main_rp_keyboard, phone_number_rp_keyboard
from database.student_repo import StudentRepo
from aiogram.fsm.context import FSMContext
from states.loging_state import  Log, AddOneTimelesson
from email_validator import validate_email, EmailNotValidError
from Utilis.Validator import Validator
from keyboards.registration_keyboard import registration
from keyboards.keyboards_builder import SlotCallback, slots_keyboard, teacher_aprove_keyboard, one_time_lesson_keyboard
from keyboards.keyboards import onetime_lesson_kb
from handlers.base_handlers import lesson_db
from config import days, id_teacher
from datetime import datetime, timedelta
from config import id_admin, id_teacher



router = Router()
student_db = StudentRepo("database/bot_db.db")


@router.message(Command('log'))
async def loging(message: Message, state: FSMContext):
    if student_db.get_student(message.from_user.id):
        if not student_db.check_if_logged(message.from_user.id):
            await state.set_state(Log.password)
            await message.answer("Введіть будь ласка свій пароль: ")
        else:
            await message.answer("Ви вже в своєму аккаунті")
    else:
        await message.answer("Схоже ви ще не зареєструвалися на нашій платформі щоб це змінити пропишіть комнаду /reg")



@router.message(Log.password)
async def log_password(message: Message, state:FSMContext):
    await state.update_data(password = message.text)
    hash = student_db.get_hash(message.from_user.id)[0]
    dict = await state.get_data()
    if Validator.check_password(dict.get("password"), hash):
        await message.answer("вхід в акаунт пройшов успішно")
        student_db.login_user(message.from_user.id)
        student_db.update_activity(message.from_user.id)
        await state.clear()
    else:
        print("wrong")
        await message.answer("Схоже ви ввели неправильний пароль, спробуйте ще раз")
        await state.set_state(Log.password)

@router.callback_query(F.data == "add_lesson")
async def add_lesson(callback:CallbackQuery):
    if lesson_db.show_free_slots():
        text =  (
            "📅 <b>Оберіть вільний слот</b>\n\n"
            "Обраний слот стане вашим <b>постійним часом для занять</b>. "
            "Бот автоматично створюватиме уроки на цей день і час щотижня.\n\n"
            "💡 Якщо ви хочете додати <b>лише один одноразовий урок</b>, "
            "натисніть кнопку <b>«➕ Додати одноразовий урок»</b> нижче 👇"
        )
    else:
        text = (
            "😔 <b>Наразі немає вільних слотів</b>\n\n"
            "На жаль, зараз усі постійні слоти для занять зайняті. "
            "Щойно з’явиться вільний час, ви зможете обрати його для регулярних занять.\n\n"
            "💡 Якщо вам потрібен <b>лише один одноразовий урок</b>, "
            "ви все одно можете його додати, натиснувши кнопку "
            "<b>«➕ Додати одноразовий урок»</b> нижче 👇"
        )
    await callback.message.answer(text=text, parse_mode="HTML", reply_markup= await slots_keyboard("take", 0))
    await callback.answer(" ")
@router.callback_query(SlotCallback.filter(F.action == "take"))
async def take_lesson_callback( callback: CallbackQuery, callback_data: SlotCallback):
    slot_id = callback_data.slot_id
    student_name = student_db.show_profile_data(callback.from_user.id)[0]
    slot = lesson_db.show_slot(slot_id)
    day_of_slot = days.get(slot[1]) + " о "+ slot[3][0:5]
    await callback.message.edit_text("Очікуєм на відповідь від вчителя")
    await callback.bot.send_message(chat_id=id_teacher, text= f"Учень: {student_name} \nхоче взяти слот в : {day_of_slot}", reply_markup=await teacher_aprove_keyboard(slot_id, callback.from_user.id))

@router.callback_query(F.data == "add_single_lesson")
async def adding_one_lesson(callback:CallbackQuery, state: FSMContext):
    text = (
        "📅 <b>Введіть дату та час бажаного уроку</b>\n\n"
        "Будь ласка, вкажіть дату та час у наступному форматі:\n\n"
        "👉 <code>2026-08-12 16:00:00</code>\n\n"
        "Формат: <b>РРРР-ММ-ДД ГГ:ХХ:СС</b>\n\n"
        "Наприклад, якщо ви хочете провести урок "
        "<b>12 серпня 2026 року о 16:00</b>, введіть:\n"
        "<code>2026-08-12 16:00:00</code>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(AddOneTimelesson.waiting_for_date)


@router.message(AddOneTimelesson.waiting_for_date)
async def get_time_for_onetime_lesson(message: Message, state: FSMContext):
    try:
        lesson_datetime = datetime.strptime(
            message.text,
            "%Y-%m-%d %H:%M:%S"
        )

    except ValueError:
        await message.answer(
            "❌ <b>Неправильний формат дати.</b>\n\n"
            "Будь ласка, введіть дату у форматі:\n"
            "<code>2026-08-12 16:00:00</code>",
            parse_mode="HTML"
        )
        return

    await state.update_data(
        lesson_datetime=lesson_datetime
    )

    await message.answer(
        f"✅ <b>Дата уроку:</b>\n\n"
        f"📅 {lesson_datetime.strftime('%d.%m.%Y')}\n"
        f"🕐 {lesson_datetime.strftime('%H:%M')}\n\n"
        f"Все правильно?",
        parse_mode="HTML",
        reply_markup= onetime_lesson_kb
    )


@router.callback_query(F.data == "cancel_onetimelesson_request")
async def cancel_request(callback: CallbackQuery, state:FSMContext):
    text = (
        "📅 <b>Введіть дату та час бажаного уроку</b>\n\n"
        "Будь ласка, вкажіть дату та час у наступному форматі:\n\n"
        "👉 <code>2026-08-12 16:00:00</code>\n\n"
        "Формат: <b>РРРР-ММ-ДД ГГ:ХХ:СС</b>\n\n"
        "Наприклад, якщо ви хочете провести урок "
        "<b>12 серпня 2026 року о 16:00</b>, введіть:\n"
        "<code>2026-08-12 16:00:00</code>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(AddOneTimelesson.waiting_for_date)


@router.callback_query(F.data == "send_onetimelesson_request")
async def send_request(callback: CallbackQuery, state: FSMContext):
    student_id = callback.from_user.id
    student_name = student_db.show_profile_data(student_id)[0]
    start_time = await state.get_value("lesson_datetime")
    end_time = start_time + timedelta(hours=1)
    request_id = lesson_db.request_onetimelesson(student_id,start_time,end_time)
    if request_id:
        text = (
            "📩 <b>Новий запит на одноразовий урок</b>\n\n"
            f"👤 Учень: <b>{student_name}</b>\n"
            f"📅 Дата: <b>{start_time.strftime('%d.%m.%Y')}</b>\n"
            f"🕐 Час: <b>{start_time.strftime('%H:%M')}</b>\n\n"
            "Учень хоче додати одноразовий урок на вказаний час.\n"
            "Будь ласка, підтвердіть або відхиліть запит 👇"
        )
        await callback.bot.send_message(chat_id=id_teacher, text=text, parse_mode="HTML", reply_markup=one_time_lesson_keyboard(request_id, student_id))
        await callback.message.edit_text("""
✅ <b>Запит успішно надіслано!</b>

Ваш запит на одноразовий урок було передано вчительці. 👩‍🏫

⏳ Очікуйте на підтвердження.
Щойно вчителька прийме або відхилить запит, ви отримаєте повідомлення від бота.
""", parse_mode="HTML")

    else:
        await callback.message.edit_text("""
⚠️ <b>Не вдалося надіслати запит</b>

Під час надсилання запиту вчительці сталася помилка. 😔

Будь ласка, спробуйте ще раз трохи пізніше.
Якщо проблема повторюється, зверніться до вчительки напряму.
""", parse_mode="HTML")
    await state.clear()

