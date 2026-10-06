from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import days, id_teacher, HASH_OF_ADMIN
from keyboards.keyboards import admin_keyboard_kb, slots_admin_kb
from keyboards.keyboards_builder import delay_lesson_keyboard, student_slots_keyboard, lesson_for_admin, lesson_admin_actions_kb, show_weekdays, accept_new_slot
from database.student_repo import StudentRepo
from database.lesson_repo import LessonRepo
from datetime import datetime, date
from keyboards.keyboards_builder import   NewSlot,students_for_admin,confirm_lesson_kb, get_student_actions_keyboard,confirm_delete_student,confirm_change_balance
from states.delay_lesson_state import Delay
from states.cancel_lesson_state import Cancel
from states.admins_states import AdminState, ChangeBalanceState, NewSlotState
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

    await callback.message.edit_text(
        text="Ось список учнів:",
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
    await callback.message.edit_text(text=text, reply_markup=get_student_actions_keyboard(student_id))
    await callback.answer()


@router.callback_query(F.data.startswith("reschedule_admin:"))
async def reschedule_lesson(callback: CallbackQuery):
    data = callback.data.split(":")
    lesson_id = data[1]

@router.callback_query(F.data.startswith("delete_student:"))
async def admin_delete_student(callback: CallbackQuery):
    data = callback.data.split(":")
    student_id = data[1]

    await callback.message.edit_text("""
    ⚠️ Ви впевнені, що хочете видалити цього учня?
    
    Цю дію неможливо буде скасувати
    """, reply_markup=confirm_delete_student(student_id))


@router.callback_query(F.data.startswith("confirm_delete_student:"))
async def confirm_admin_delete_student(callback: CallbackQuery):
    data = callback.data.split(":")
    student_id = data[1]

    if student_db.delete_user_info(student_id):
        await callback.message.edit_text("""
        Учня і всю його інформацію було видалено👍
        """)
    else:
        await callback.message.edit_text("""
        Нажаль сталася помикла звернітсья до тех підтримки☹️
        """)

@router.callback_query(F.data.startswith("change_balance:"))
async def change_balance(callback:CallbackQuery, state: FSMContext):
    data = callback.data.split(":")
    student_id = data[1]
    await callback.message.answer("""
    Вкажіть на яку суму ви хочете змінити баланс учня 
    """)
    await callback.answer(" ")
    await state.set_state(ChangeBalanceState.new_balance)
    await state.update_data(student_id=student_id)


@router.message(ChangeBalanceState.new_balance)
async def checking_new_balance(message: Message, state: FSMContext):
    new_balance_from_admin = message.text
    student_id = await state.get_value("student_id")
    old_balance = student_db.show_profile_data(student_id)[4]

    try:
        new_balance = float(new_balance_from_admin)
        await message.answer(f"💰 Підтвердження зміни суми\n\nПоточна сума: {old_balance}\nНова сума: {new_balance}\n\nБудь ласка,перевірте дані та підтвердіть зміну.",
                             reply_markup=confirm_change_balance(student_id,new_balance))
    except ValueError:
        await message.answer("Введіть число")

@router.callback_query(F.data.startswith("accept_change_balance:"))
async def confirm_new_balance(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split(":")
    student_id = data[1]
    new_balance = data[2]

    success = student_db.change_balance_for_student(
        telegram_id=student_id,
        balance= new_balance
    )

    if success:
        await callback.message.answer(
            f"✅ Баланс успішно змінено на {new_balance} грн."

        )
        await callback.answer(" ")
    else:
        await callback.message.answer(
            "❌ Не вдалося змінити баланс."
        )

    await state.clear()

@router.message(F.text == "🕦Слоти")
async def show_slots_options(message: Message):
    await message.answer("👇Оберіть кнопку",reply_markup=slots_admin_kb)

@router.message(F.text == "➕ Додати новий слот")
async def adding_new_slot(message: Message):
    await message.answer("😀 Супер тепер спочатку оберіть на який день потрібно зарезервувати слот", reply_markup=show_weekdays())

@router.message(F.text == "⬅️ Повернутися назад до Панелі")
async def back_to_panel(message: Message):
    await message.answer("👇Оберіть кнопку",reply_markup=admin_keyboard_kb)

@router.callback_query(F.data.startswith("weekday_"))
async def hour_for_new_slot(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    weekday = data[1]

    await callback.message.edit_text("🕐 Введіть час початку слоту у форматі ГГ:ХХ:СС\n\nНаприклад: 14.00.00")
    await state.set_state(NewSlotState.new_hour)
    await state.update_data(day=weekday)

@router.message(NewSlotState.new_hour)
async def duration_for_slot(message: Message, state: FSMContext):
    time_from_admin = message.text
    try:
        time = datetime.strptime(time_from_admin, "%H.%M.%S")
        await state.update_data(hour=time_from_admin)
        await message.answer("⏳ Супер тепер введіть скільки має тривати урок в хвилинах")
        await state.set_state(NewSlotState.new_duration)
    except ValueError:
        await message.answer("Неправильний формат спробуй ще раз")


@router.message(NewSlotState.new_duration)
async def accepting_duration_for_slot(message: Message, state: FSMContext):
    duration_from_admin = message.text
    try:
        duration = int(duration_from_admin)
        if duration <= 120:
            data = await state.get_data()
            hour = data["hour"]
            day = days[int(data["day"])]
            message_for_admin = (
                f"🆕 <b>Новий слот</b>\n\n"
                f"📅 День: <b>{day}</b>\n"
                f"🕐 Час: <b>{data['hour']}</b>\n"
                f"⏱ Тривалість: <b>{duration} хв.</b>\n\n"
                f"Перевірте дані та підтвердьте створення слоту 👇"
            )
            await message.answer(message_for_admin, parse_mode="HTML", reply_markup=accept_new_slot(data["day"], hour, duration))
            await state.clear()
        else:
            await message.answer("Ви ввели завелике число")
    except ValueError as e:
        print(e)
        await message.answer("Введіть число")


@router.callback_query(NewSlot.filter())
async def confirmation_new_slot(callback:CallbackQuery, callback_data: NewSlot):
    weekday, time, duration = callback_data.weekday, callback_data.time.replace(".", ":"), callback_data.duration
    if lesson_db.add_new_slot(weekday,time,duration):
        await callback.message.answer("Новий слот додано ✅")
    else:
        await callback.message.answer("Нажаль сталася помикла ☹️")

@router.callback_query(F.data =="decline_new_slot")
async def decline_new_slot(callback: CallbackQuery):
    await callback.message.answer("😉 Давайте спробуємо знову\nоберіть на який день потрібно зарезервувати слот",reply_markup=show_weekdays())
