from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import days
from keyboards.keyboards import main_rp_keyboard, profile_keyboard, delay_lesson_kb
from keyboards.keyboards_builder import delay_lesson_keyboard, student_slots_keyboard
from database.student_repo import StudentRepo
from database.lesson_repo import LessonRepo
from datetime import datetime
from keyboards.keyboards_builder import LessonCallback, teacher_aprove_lesson_keyboard, teacher_aprove_cancel_keyboard, SlotCallback, slots_keyboard, SlotChangeCallback, teacher_slot_decision_keyboard
from states.delay_lesson_state import Delay
from states.cancel_lesson_state import Cancel
from handlers.base_handlers import student_db,lesson_db
from Utilis.Date import Date

router = Router()

@router.callback_query(F.data == "delay_lesson")
async def delay(callback: CallbackQuery):
    await callback.message.answer("оберіть урок який ви хочете перенести", reply_markup=await delay_lesson_keyboard(callback.from_user.id, "delay"))
    await callback.answer("")


@router.callback_query(F.data == "cancel_lesson")
async def cancel(callback: CallbackQuery):
    await callback.message.answer("оберіть урок який ви хочете відмінити",
                                  reply_markup=await delay_lesson_keyboard(callback.from_user.id, "cancel"))
    await callback.answer("")

@router.callback_query(LessonCallback.filter(F.action == "cancel"))
async def cancel_lesson(callback: CallbackQuery, state: FSMContext, callback_data: LessonCallback):
    await callback.message.edit_text("""
    Напишіть причину:
    """)
    await state.set_state(Cancel.reason)
    await state.update_data(
        lesson_id = callback_data.lesson_id,
        student_id = callback_data.student_id,
    )

@router.callback_query(F.data == "delay_slots")
async def delay_slots(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        "Виберіть, який слот ви хочете змінити",
        reply_markup=await student_slots_keyboard("delay_slot", callback.from_user.id)
    )

@router.callback_query(SlotCallback.filter(F.action == "delay_slot"))
async def delay_slot(callback: CallbackQuery, callback_data: SlotCallback):
    old_slot_id = callback_data.slot_id
    slots = lesson_db.show_slots()
    has_free_slots = any(slot[2] == "free" for slot in slots)
    if not has_free_slots:
        await callback.message.edit_text(
            "😔 На цей момент немає вільних слотів."
        )
        return
    await callback.message.edit_text(
        "Виберіть новий слот:",
        reply_markup=await slots_keyboard(
            action="change",
            old_slot_id=old_slot_id
        )
    )

@router.callback_query(SlotChangeCallback.filter(F.action == "change"))
async def request_for_change_slot(callback: CallbackQuery, callback_data: SlotChangeCallback):
    user_id = callback.from_user.id
    user_name = student_db.show_profile_data(user_id)[0]
    old_id = callback_data.old_slot_id
    old_weekday = days[lesson_db.show_slot(old_id)[1]]
    old_time = lesson_db.show_slot(old_id)[3][:-3]
    new_id = callback_data.slot_id
    new_weekday = days[lesson_db.show_slot(new_id)[1]]
    new_time = lesson_db.show_slot(new_id)[3][:-3]
    await callback.message.edit_text("Ваш запит надіслано вчителеві")
    await callback.bot.send_message(chat_id=525989603,
        text= f"""
        📚 <b>Запит на зміну постійного слота</b>

👤 <b>Учень:</b> {user_name}

📅 <b>Поточний слот:</b>
• {old_weekday} о {old_time}

🔄 <b>Новий слот:</b>
• {new_weekday} о {new_time}


━━━━━━━━━━━━━━━━━━━━━━
Підтвердити зміну постійного розкладу?
        """, parse_mode="HTML", reply_markup=await teacher_slot_decision_keyboard(
    student_id=user_id,
    old_slot_id=old_id,
    new_slot_id=new_id
)
                                    )


@router.message(Cancel.reason)
async def write_reason(message: Message, state: FSMContext):
    user_input = message.text

    lesson_id = await state.get_value("lesson_id")
    student_name = student_db.show_profile_data(message.from_user.id)[0]
    lesson_date = [lesson[3] for lesson in lesson_db.show_lesson_for_student(message.from_user.id) if
                   lesson[0] == lesson_id]
    lesson_date_dt = Date.parse_user_datetime(lesson_date[0][:-3])
    formated_date = lesson_date_dt.strftime("%d.%m.%Y o %H:%M")

    lesson_db.create_cancel_request(lesson_id,user_input,"student")

    await message.answer("""
    Ми відправили ваш запит вчителю очікуйте на підтвердження
    """)

    await message.bot.send_message(
        chat_id=525989603,
        text=f"""
    📩 Запит на скасування уроку

    👤 Учень:   {student_name} 
    ⁉️ Причина: {user_input}
    📅 Поточний урок:  {formated_date} 

    Підтвердити перенесення?
    """, reply_markup=await teacher_aprove_cancel_keyboard(await state.get_value("lesson_id"),
                                                           await state.get_value("student_id"))
    )




@router.callback_query(LessonCallback.filter(F.action == "delay"))
async def choose_date(callback: CallbackQuery, state: FSMContext, callback_data: LessonCallback):
    await callback.message.edit_text("""
📅 На коли ви хочете перенести урок?

Будь ласка, введіть дату та час у форматі:
YYYY-MM-DD HH:MM

Наприклад:
2026-05-15 18.30
    """)
    await state.set_state(Delay.waiting)
    await state.update_data(
        lesson_id = callback_data.lesson_id,
        student_id = callback_data.student_id,
        new_date = callback_data.new_date
    )

@router.message(Delay.waiting)
async def send_reason(message:Message, state: FSMContext):
    user_input = message.text.strip()

    dt = Date.parse_user_datetime(user_input)

    if not dt:
        await message.answer(
            "❌ Неправильний формат!\n\n"
            "Введіть дату так:\n"
            "YYYY-MM-DD HH:MM\n\n"
            "Наприклад:\n"
            "2026-05-15 18.30"
        )
        return

    await state.update_data(new_date= dt)

    await state.set_state(Delay.sending)

    await message.answer("Напишіть причину:")

@router.message(Delay.sending)
async def sending_data(message: Message, state: FSMContext):
    lesson_id = await state.get_value("lesson_id")
    student_name = student_db.show_profile_data(message.from_user.id)[0]
    lesson_date = [lesson[3] for lesson in lesson_db.show_lesson_for_student(message.from_user.id) if lesson[0] == lesson_id]
    user_input = message.text.strip()

    reason = message.text.strip()
    new_date = await state.get_value("new_date")
    formated_new_date = new_date.strftime("%d.%m.%Y o %H:%M")
    lesson_date_dt = Date.parse_user_datetime(lesson_date[0][:-3])
    formated_date = lesson_date_dt.strftime("%d.%m.%Y o %H:%M")


    if not reason:
        await message.answer("Будь ласка, напишіть причину перенесення.")
        return

    await state.update_data(reason=reason)
    lesson_db.create_rescheduled_request(lesson_id,new_date,reason)

    await message.answer("ваші дані відправилися вчителеві на підтвердження!")
    await message.bot.send_message(
        chat_id=525989603,
        text= f"""
📩 Запит на перенесення уроку

👤 Учень:   {student_name} 
⁉️ Причина: {await state.get_value("reason")}
📅 Поточний урок:  {formated_date} 
🔄 Нова дата:  {formated_new_date}

Підтвердити перенесення?
""",reply_markup = await teacher_aprove_lesson_keyboard(await state.get_value("lesson_id"),await state.get_value("student_id"), new_date.strftime("%Y-%m-%d %H.%M"))
    )

    await state.clear()


@router.callback_query(F.data == "reject_slot")
async def reject_slot(callback: CallbackQuery):
   user_id = callback.from_user.id
   await callback.message.answer("""
       Виберіть який слот ви хочете відмінити:
       """, reply_markup= await student_slots_keyboard("cancel_slot",user_id))
   await callback.answer(
           "⚠️ Після натискання наступної кнопки слот буде остаточно видалений.",
           show_alert=True
       )

@router.callback_query(SlotCallback.filter(F.action == "cancel_slot"))
async def cancel_slot(callback: CallbackQuery, callback_data: SlotCallback):
    user_id = callback.from_user.id
    slot_id = callback_data.slot_id
    user_info = student_db.show_profile_data(user_id)
    slots_info = lesson_db.show_slot(slot_id)
    day = days[slots_info[1]]
    time = slots_info[3][:-3]
    username = user_info[0]

    if lesson_db.cancel_slot(user_id, slot_id):
        await callback.message.answer("""
        Ваш слот був успішно видалений тепер 
        всі майбутні уроки будуть видалені
        """)
        await callback.bot.send_message(chat_id=525989603, text=f"""
        Учень: {username}
        Відмінив слот: {day} о {time}
        """)

