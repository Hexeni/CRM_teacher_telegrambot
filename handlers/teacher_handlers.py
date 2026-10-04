import datetime

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from keyboards.keyboards import main_rp_keyboard, phone_number_rp_keyboard
from database.student_repo import StudentRepo
from aiogram.fsm.context import FSMContext
from states.registration_state import Reg
from email_validator import validate_email, EmailNotValidError
from Utilis.Validator import Validator
from Utilis.Date import Date
from keyboards.techer_keyboard import slot_keyboard, AcceptPaymentTeacher
from handlers.base_handlers import lesson_db, student_db
from keyboards.keyboards_builder import teacher_aprove_keyboard, AproveSlotCallback,LessonCallback, TeacherSlotDecisionCallback, OneTimeLessonCallback
from  states.delay_lesson_state import RejectDelay
from keyboards.techer_keyboard import PasswordChangeCallback
from Middelwares.admin_middelware import AdminMiddleware

router = Router()
router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())

@router.callback_query(AproveSlotCallback.filter(F.action == "accept_slot"))
async def add_slot_in_db(callback: CallbackQuery, callback_data: AproveSlotCallback):
    slot_id = callback_data.slot_id
    student_id = callback_data.student_id
    slot = lesson_db.show_slot(slot_id)
    date_of_slot = Date.find_next_weekday(slot[1] - 1)
    time_str = slot[3]
    duration = slot[-1]
    hour, minute, second = map(int, time_str.split(":"))

    datetime_of_begining = datetime.datetime(
        date_of_slot.year,
        date_of_slot.month,
        date_of_slot.day,
        hour,
        minute,
        second
    )
    datetime_of_ending = datetime_of_begining + datetime.timedelta(minutes=duration)
    lesson_db.approve_slot_and_create_lesson(slot_id, student_id, datetime_of_begining, datetime_of_ending)

    await callback.answer(" ")
    await callback.bot.send_message(
        chat_id= student_id,
        text="Ваш слот підтверджено"
    )
    await callback.message.answer("Супер інформація обновиласфя в базі даних")

@router.callback_query(AproveSlotCallback.filter(F.action == "reject_slot"))
async def reject_slot(callback:CallbackQuery, callback_data: AproveSlotCallback):
    student_id = callback_data.student_id

    await callback.bot.send_message(
        chat_id=student_id,
        text= "Нажаль вчитель відхилив ваше прохання звяжіться з ним щоб дізнатися причину"
    )
    await callback.message.answer("Ми надіслали учню повідомлення про відхилення")

@router.callback_query(LessonCallback.filter(F.action == "accept_delay"))
async def accept_delay(callback: CallbackQuery, callback_data: LessonCallback):
    fixed = callback_data.new_date.replace(".",":")
    lesson = [lesson for lesson in lesson_db.show_lesson_for_student(callback_data.student_id) if lesson[0] == callback_data.lesson_id][0]
    new_date_beginning = datetime.datetime.fromisoformat(fixed)
    old_date_beginning = datetime.datetime.fromisoformat(lesson[3])
    old_date_end = datetime.datetime.fromisoformat(lesson[4])
    delta = old_date_end - old_date_beginning
    new_date_ending = new_date_beginning + delta
    lesson_db.update_lesson(callback_data.lesson_id, new_date_beginning, new_date_ending,True)
    formatted_date = new_date_beginning.strftime(
        "%d.%m.%Y o %H:%M"
    )
    await callback.bot.send_message(
        chat_id=callback_data.student_id,
        text=(
            "✅ Викладач підтвердив перенесення уроку!\n\n"
            f"📅 Нова дата: {formatted_date}"
        )
    )

    await callback.message.edit_text(
        "✅ Перенесення уроку підтверджено.\n\n"
        f"📅 Нова дата: {formatted_date}"
    )

    await callback.answer("Перенесення підтверджено")



@router.callback_query(LessonCallback.filter(F.action == "reject_delay"))
async def reject_delay(
    callback: CallbackQuery,
    callback_data: LessonCallback,
    state: FSMContext
):
    await state.update_data(
        lesson_id=callback_data.lesson_id,
        student_id=callback_data.student_id
    )

    await state.set_state(RejectDelay.waiting_reason)

    await callback.message.edit_text(
        "Вкажіть, будь ласка, причину відхилення:"
    )

    await callback.answer()

@router.message(RejectDelay.waiting_reason)
async def get_reject_reason(
    message: Message,
    state: FSMContext
):
    reason = message.text.strip()

    if not reason:
        await message.answer("Введіть причину.")
        return

    data = await state.get_data()

    lesson_id = data["lesson_id"]
    student_id = data["student_id"]

    lesson_db.update_lesson(
        lesson_id,
        "none",
        "none",
        False
    )

    await message.bot.send_message(
        chat_id=student_id,
        text=(
            "❌ Викладач відхилив перенесення уроку.\n\n"
            f"📝 Причина: {reason}"
        )
    )

    await message.answer(
        "✅ Відмову надіслано учневі."
    )

    await state.clear()

@router.callback_query(LessonCallback.filter(F.action == "accept_cancel"))
async def accept_cancel(callback: CallbackQuery, callback_data: LessonCallback):
    lesson_id = callback_data.lesson_id
    lesson_db.cancel_lesson(lesson_id)
    await callback.bot.send_message(
        chat_id=callback_data.student_id,
        text=(
            "✅ Викладач підтвердив відміну уроку!"
        )
    )

    await callback.message.edit_text(
        "✅ Відміну уроку підтверджено.\n\n"
    )

    await callback.answer("Перенесення підтверджено")



@router.callback_query(LessonCallback.filter(F.action == "reject_cancel"))
async def reject_cancel(callback: CallbackQuery, callback_data: LessonCallback):
    lesson_id = callback_data.lesson_id
    lesson_db.cancel_lesson(lesson_id, False)


    await callback.bot.send_message(
        chat_id=callback_data.student_id,
        text=(
            "❌ Викладач не підтвердив скасування уроку.\n\n"
            "📅 Урок залишається у вашому розкладі."
        )
    )

    await callback.message.edit_text(
        "❌ Запит на скасування уроку відхилено.\n\n"
        "Урок залишається активним."
    )

    await callback.answer("Скасування відхилено")


@router.callback_query(TeacherSlotDecisionCallback.filter(F.action == "accept"))
async def accept_slot_change(
    callback: CallbackQuery,
    callback_data: TeacherSlotDecisionCallback
):
    success = lesson_db.update_slot_for_student(
        old_slot_id=callback_data.old_slot_id,
        new_slot_id=callback_data.new_slot_id,
        student_id=callback_data.student_id
    )

    if not success:
        await callback.answer(
            "Не вдалося змінити слот",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        callback.message.html_text
        + "\n\n✅ <b>Зміну підтверджено</b>",
        parse_mode="HTML"
    )

    await callback.bot.send_message(
        chat_id=callback_data.student_id,
        text="""
✅ <b>Викладач підтвердив зміну слота</b>

Ваш постійний розклад успішно оновлено.
Наступні заняття проходитимуть за новим слотом.
""",
        parse_mode="HTML"
    )

    await callback.answer("Слот успішно змінено")

@router.callback_query(TeacherSlotDecisionCallback.filter(F.action == "reject"))
async def reject_slot_change(
    callback: CallbackQuery,
    callback_data: TeacherSlotDecisionCallback
):
    await callback.message.edit_text(
        callback.message.html_text
        + "\n\n❌ <b>Запит відхилено</b>",
        parse_mode="HTML"
    )

    await callback.bot.send_message(
        chat_id=callback_data.student_id,
        text="""
😔 <b>На жаль, викладач не підтвердив зміну слота</b>

Ваш поточний розклад залишається без змін.
""",
        parse_mode="HTML"
    )

    await callback.answer("Запит відхилено")

@router.callback_query(PasswordChangeCallback.filter(F.action == "accept"))
async def accept_password_change_handler(
    callback: CallbackQuery,
    callback_data: PasswordChangeCallback
):

    telegram_id = student_db.accept_password_change(
        callback_data.request_id
    )

    if telegram_id is None:
        await callback.answer(
            "Запит не знайдено або його вже оброблено.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "✅ <b>Запит підтверджено</b>\n\n"
        "Пароль користувача успішно змінено.",
        parse_mode="HTML"
    )

    try:
        await callback.bot.send_message(
            chat_id=telegram_id,
            text=(
                "✅ <b>Ваш пароль успішно змінено</b>\n\n"
                "Адміністратор підтвердив запит.\n"
                "Тепер ви можете використовувати "
                "новий пароль."
            ),
            parse_mode="HTML"
        )
    except Exception as error:
        print(
            "Не вдалося повідомити користувача: "
            f"{error}"
        )

    await callback.answer("Пароль змінено")
    student_db.change_profile_data(telegram_id,"is_loged","0")

@router.callback_query(PasswordChangeCallback.filter(F.action == "reject"))
async def reject_password_change_handler(
    callback: CallbackQuery,
    callback_data: PasswordChangeCallback
):
    telegram_id = student_db.reject_password_change(
        callback_data.request_id
    )

    if telegram_id is None:
        await callback.answer(
            "Запит не знайдено або його вже оброблено.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "❌ <b>Запит відхилено</b>\n\n"
        "Пароль користувача залишився без змін.",
        parse_mode="HTML"
    )

    try:
        await callback.bot.send_message(
            chat_id=telegram_id,
            text=(
                "❌ <b>Запит на зміну пароля відхилено</b>\n\n"
                "Ваш старий пароль залишився активним.\n"
                "За додатковою інформацією зверніться "
                "до адміністратора."
            ),
            parse_mode="HTML"
        )
    except Exception as error:
        print(
            "Не вдалося повідомити користувача: "
            f"{error}"
        )

    await callback.answer("Запит відхилено")

@router.callback_query(AcceptPaymentTeacher.filter())
async def accept_payment(callback: CallbackQuery, callback_data: AcceptPaymentTeacher):
    student_id = callback_data.student_id
    pending_payment = student_db.show_pending_payments(student_id)[0]
    payment_id, sum = pending_payment[0], pending_payment[2]
    if callback_data.action == "accept":
        if student_db.change_status_of_payment(payment_id,"approved"):
            if student_db.adding_payment(student_id,sum):
                await callback.message.edit_text("""
                Супер, ми надіслали підтвердження оплати учню 
                """)
                await callback.bot.send_message(chat_id=student_id, text="""
                Вчитель підтвердив надходження коштів, тепер у вашому балансі повина відображатися задана сума
                """)
                await callback.bot.send_sticker(chat_id=student_id, sticker="CAACAgIAAxkBAAINX2qPc03Wy_C2bZTXyq_ZsY6XFRp4AAIRJAACGB2xSvt5jn7OmeYPPQQ")


    elif callback_data.action == "reject":
        if student_db.change_status_of_payment(payment_id, "canceled"):
            await callback.message.edit_text("""
                            Супер, ми надіслали учню повідомлення
                            """)
            await callback.bot.send_message(chat_id=student_id, text="""
                            Нажаль викладач не підвтердив отримання коштів, звяжіться з ним як найшвидше щоб вирішити це питання
                            """)




@router.callback_query(OneTimeLessonCallback.filter())
async def process_one_time_lesson(callback: CallbackQuery, callback_data: OneTimeLessonCallback):
    lesson_id = callback_data.request_id
    action = callback_data.action
    student_id = callback_data.student_id
    if action == "accept":
        status = "active_onetime_lesson"
        text = "✅ <b>Одноразовий урок підтверджено.</b>"

    elif action == "reject":
        status = "reject_onetime_lesson"
        text = "❌ <b>Запит на одноразовий урок відхилено.</b>"

    else:
        await callback.answer(
            "❌ Невідома дія",
            show_alert=True
        )
        return

    if lesson_db.change_status_for_one_time_lesson(lesson_id, status):
        await callback.message.edit_text(text=text, parse_mode="HTML")
        await callback.bot.send_message(chat_id=student_id, text=text, parse_mode="HTML")

    else:
        await callback.answer(
            "❌ Не вдалося змінити статус уроку.",
            show_alert=True
        )

        return

    await callback.answer()
