from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import days, id_teacher, HASH_OF_ADMIN
from keyboards.keyboards import main_rp_keyboard, profile_keyboard, delay_lesson_kb, admin_keyboard_kb
from keyboards.keyboards_builder import delay_lesson_keyboard, student_slots_keyboard, lesson_for_admin, lesson_admin_actions_kb
from database.student_repo import StudentRepo
from database.lesson_repo import LessonRepo
from datetime import datetime, date
from keyboards.keyboards_builder import LessonCallback, teacher_aprove_lesson_keyboard, teacher_aprove_cancel_keyboard, SlotCallback, slots_keyboard, SlotChangeCallback, teacher_slot_decision_keyboard, students_for_admin,confirm_lesson_kb
from states.delay_lesson_state import Delay
from states.cancel_lesson_state import Cancel
from states.admins_states import AdminState
from handlers.base_handlers import student_db,lesson_db
from Utilis.Date import Date
from Utilis.Validator import Validator
from Middelwares.admin_middelware import AdminMiddleware


router = Router()

router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())

@router.message(Command("admin"))
async def check_admin(message: Message, state: FSMContext):
    id_of_user = message.from_user.id
    if id_of_user == id_teacher:
        await message.answer("Введіть спеціальний пароль:")
        await state.set_state(AdminState.password)
    else:
        await message.answer("Нажаль у вашого аккаунта немає прав на виконання цієї команди")

@router.message(AdminState.password)
async def check_password_for_admin_routes(message: Message, state: FSMContext):
    possible_password = message.text.strip()
    hash_admin = HASH_OF_ADMIN.encode()
    if Validator.check_password(possible_password, hash_admin):
        await message.answer("Ласкаво просимо містер Кнур🐷")
        await message.bot.send_sticker(chat_id=message.from_user.id, sticker="CAACAgQAAxkBAAIMNWqKIZSPT7bsU9uBrtrfDOB5DpttAALbEwACfMC7AAH0R4myoXU4Vz0E", reply_markup=admin_keyboard_kb)
        await state.clear()
    else:
        await message.answer("Неправильний пароль")


@router.message(F.text == "📚Уроки")
async def making_keyboard_lessons(message: Message):
    today = date.today()
    lessons = lesson_db.get_lessons_by_date(today)
    if lessons:
        text = (
            f"📚 <b>Уроки на сьогодні</b>\n"
            f"📅 <b>{today.strftime('%d.%m.%Y')}</b>\n\n"
            f"Оберіть урок 👇"
        )
    else:
        text =  (
            f"📅 <b>{today.strftime('%d.%m.%Y')}</b>\n\n"
            f"😴 На цей день уроків немає."
        )
    await message.answer(text, reply_markup=lesson_for_admin(lessons, today), parse_mode="HTML")

@router.callback_query(F.data.startswith("lesson_date:"))
async def change_lesson_date(callback: CallbackQuery):

    date_str = callback.data.split(":")[1]

    current_date = datetime.strptime(
        date_str,
        "%Y-%m-%d"

    ).date()

    lessons = lesson_db.get_lessons_by_date(current_date)

    if lessons:
        text = (
            f"📅 <b>Уроки на {current_date.strftime('%d.%m.%Y')}</b>\n\n"
            f"Оберіть урок 👇"
        )
    else:
        text = (
            f"📅 <b>{current_date.strftime('%d.%m.%Y')}</b>\n\n"
            f"😴 На цей день уроків немає."
        )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=lesson_for_admin(
            lessons,
            current_date
        )
    )

    await callback.answer()

@router.callback_query(F.data.startswith("lesson:"))
async def show_info(callback: CallbackQuery):

    data = callback.data.split(":")

    lesson_id = int(data[1])
    student_id = int(data[2])

    lesson = lesson_db.get_lesson(lesson_id)

    if not lesson:
        await callback.answer(
            "Урок не знайдено",
            show_alert=True
        )
        return

    (
        lesson_id,
        start_time,
        end_time,
        status,
        is_paid,
        name,
        telegram_id
    ) = lesson

    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    payment = "✅ Оплачено" if is_paid else "❌ Не оплачено"

    text = (
        f"📚 <b>Інформація про урок</b>\n\n"

        f"👤 <b>Учень:</b> {name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n\n"

        f"📅 <b>Дата:</b> {start.strftime('%d.%m.%Y')}\n"
        f"🕐 <b>Час:</b> {start.strftime('%H:%M')}–{end.strftime('%H:%M')}\n\n"

        f"💳 <b>Оплата:</b> {payment}\n"
        f"📌 <b>Статус:</b> {status}"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=lesson_admin_actions_kb(lesson_id,student_id,lesson_date=start.date().isoformat(),is_paid=is_paid)
    )

    await callback.answer()

@router.callback_query(F.data.startswith("mark_paid:"))
async def mark_as_paid(callback: CallbackQuery):
    data = callback.data.split(":")

    lesson_id = data[1]
    student_id = data[2]
    if student_db.pay_for_lesson(lessons_to_pay=[lesson_id], sum_to_pay=0, telegram_id=student_id):
        text = "Супер статус урока був змінений на оплачено"
    else:
        text = "Нажаль не вийшло змінити статус урока, виникла невідома помилка"
    await callback.message.edit_text(text=text)

@router.callback_query(F.data.startswith("cancel_admin:"))
async def cancel_lesson_admin(callback: CallbackQuery):
   lesson_id = int(callback.data.split(":")[1])

   await callback.message.edit_text(
       "<b>Ви дійсно хочете скасувати урок?</b>\n\n"
       "Після пітвердження урок буде скасовано.",
       reply_markup=confirm_lesson_kb(lesson_id),
       parse_mode="HTML"
   )
   await callback.answer()

@router.callback_query(F.data.startswith("confirm_cancel_lesson:"))
async def confirm_cancel_lesson(callback: CallbackQuery):
    data = callback.data.split(":")

    lesson_id = data[1]
    info_for_lesson = lesson_db.get_lesson(lesson_id)
    date_of_lesson, name_of_student, id_student = info_for_lesson[1], info_for_lesson[5], info_for_lesson[6]
    date_of_lesson_formated = datetime.strptime(date_of_lesson, "%Y-%m-%d %H:%M:%S")
    date_of_lesson_pretty = date.strftime(date_of_lesson_formated, "%d.%m.%Y o %H:%M")
    try:
        lesson_db.cancel_lesson(lesson_id)
        text = f"Урок в {date_of_lesson_pretty} для {name_of_student} був скасований"
        await callback.bot.send_message(chat_id=id_student, text=f"""
    ⚠️ <b>УРОК СКАСОВАНО</b>

    👨‍🏫 Вчитель скасував ваш урок.

    📅 <b>Дата:</b> {date_of_lesson_pretty}

    ❗ Цей урок більше не відбудеться.
    """, parse_mode="HTML")
    except Exception as e:
        print(e)
        text = f"Сталася помилка і урок в {date_of_lesson_pretty} для {name_of_student} не скасувався"
    await callback.message.edit_text(text=text)

@router.callback_query(F.data.startswith("cancel_cancel_lesson:"))
async def cancel_cancel_lesson(callback: CallbackQuery):

    lesson_id = int(callback.data.split(":")[1])

    await callback.message.edit_text(
        "✅ Скасування уроку відмінено.\n\n"
        "Урок залишився активним."
    )

    await callback.answer()

@router.message(F.text == "👨‍🎓Учні")
async def show_students(message: Message):
    students = student_db.show_students()
    if students:
        text = "Ось список студентів:"
        await message.answer(text=text, reply_markup=students_for_admin(students))
    else:
        await message.answer(text="Сталася якась помилка")

@router.callback_query(F.data.startswith("students_page_"))
async def change_students_page(callback: CallbackQuery):

    page = int(callback.data.split("_")[-1])

    students = student_db.show_students()

    await callback.message.edit_reply_markup(
        reply_markup=students_for_admin(
            students=students,
            page=page
        )
    )

    await callback.answer()

@router.callback_query(F.data.startswith("student_"))
async def show_students_profile(callback: CallbackQuery):

    data = callback.data.split("_")
    student_id = data[1]
    student = student_db.get_student_infor_for_admin(student_id)
    print(student)
    next_lesson = student["next_lesson"]
    if next_lesson:
        lesson_date = datetime.strptime(next_lesson,
                                        "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y o %H:%M")
    else:
        lesson_date = "Немає поки наступного уроку"
    text = f"""
    👤 Інформація про учня

👨‍🎓 Ім’я: {student["name"]}
🔐 Логін: {student["login"]}
🆔 Telegram ID: {student_id}

💰 Баланс: {student["balance"]} ₴

📚 Проведено уроків: {student["completed_lesson"]}
💳 Неоплачених уроків: {student["unpaid_lessons"]}
❌ Скасовано уроків: {student["canceled_lessons"]}



⏭ Наступний урок:
{lesson_date}
    """
    await callback.message.edit_text(text=text)
    await callback.answer()


@router.callback_query(F.data.startswith("reschedule_admin:"))
async def reschedule_lesson(callback: CallbackQuery):
    data = callback.data.split(":")
    lesson_id = data[1]







