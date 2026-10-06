from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from handlers.base_handlers import lesson_db,student_db
from config import days
from datetime import date, timedelta, datetime



class SlotCallback(CallbackData, prefix="lesson"):
    action: str
    slot_id : int

class SlotChangeCallback(CallbackData, prefix = "slot"):
    action: str
    old_slot_id: int
    slot_id: int

class SlotCancelCallback(CallbackData, prefix = "cancel_slot"):
    action: str


class AproveSlotCallback(CallbackData, prefix="aprove_clot"):
    action: str
    slot_id: int
    student_id: int

class LessonCallback(CallbackData, prefix="lesson_callback"):
    action: str
    lesson_id: int
    student_id: int
    new_date: str

class TeacherSlotDecisionCallback(CallbackData, prefix="teacher_slot"):
    action: str
    student_id: int
    old_slot_id: int
    new_slot_id: int

class SelectPaymentLesson(CallbackData, prefix= "pay_lesson"):
    lesson_id : int

class OneTimeLessonCallback(CallbackData, prefix="one_time_lesson"):
    action: str
    request_id: int
    student_id: int

class NewSlot(CallbackData, prefix="new_slot"):
    weekday: int
    time: str
    duration: int

async def slots_keyboard(action: str, old_slot_id: int):
    builder = InlineKeyboardBuilder()
    slots = lesson_db.show_slots()

    for slot in slots:
        if slot[2] != "free":
            continue

        slot_id = slot[0]
        weekday = slot[1]
        time = slot[3][:5]

        if action == "change":
            callback = SlotChangeCallback(
                action="change",
                old_slot_id=old_slot_id,
                slot_id=slot_id
            )
        else:
            callback = SlotCallback(
                action=action,
                slot_id=slot_id
            )

        builder.button(
            text=f"{days[weekday]} • {time}",
            callback_data=callback.pack()
        )

    builder.button(
        text="➕ Додати одноразовий урок",
        callback_data="add_single_lesson"
    )

    builder.adjust(1)
    return builder.as_markup()

async def teacher_aprove_keyboard(slot_id: int, student_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Підтвердити",
        callback_data = AproveSlotCallback(
            action = "accept_slot",
            slot_id = slot_id,
            student_id = student_id
        )
    )

    builder.button(
        text="Відхилити",
        callback_data=AproveSlotCallback(
            action = "reject_slot",
            slot_id = slot_id,
            student_id = student_id
        )
    )
    builder.adjust(2)
    return builder.as_markup()

async def delay_lesson_keyboard(student_id: int, action: str):
    builder = InlineKeyboardBuilder()
    lessons = lesson_db.show_lesson_for_student(student_id)
    sorted_lessons = sorted(lessons, key=lambda lesson: lesson[3])
    for lesson in sorted_lessons:
        if lesson[-1] != 1 and lesson [-2] != "canceled":
            date_part, time_part = lesson[3].split(" ")

            year, month, day = date_part.split("-")
            hour, minutes, seconds = time_part.split(":")

            builder.button(
                text=f"{day}.{month} o {hour}:{minutes}",
                callback_data = LessonCallback(
                    action = action,
                    lesson_id = lesson[0],
                    student_id = student_id,
                    new_date = "none"
                )
            )
    builder.adjust(1)
    return builder.as_markup()

async def teacher_aprove_lesson_keyboard(lesson_id: int, student_id: int, new_date: str):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Підтвердити",
        callback_data=LessonCallback(
            student_id=student_id,
            lesson_id= lesson_id,
            action= "accept_delay",
            new_date = new_date
        )
    )

    builder.button(
        text="Відхилити",
        callback_data=LessonCallback(
            student_id=student_id,
            lesson_id=lesson_id,
            action="reject_delay",
            new_date=new_date

        )
    )
    builder.adjust(2)
    return builder.as_markup()

async def teacher_aprove_cancel_keyboard(lesson_id: int, student_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Підтвердити",
        callback_data=LessonCallback(
            student_id=student_id,
            lesson_id= lesson_id,
            action= "accept_cancel",
            new_date="none"

        )
    )

    builder.button(
        text="Відхилити",
        callback_data=LessonCallback(
            student_id=student_id,
            lesson_id=lesson_id,
            action="reject_cancel",
            new_date="none"

        )
    )
    builder.adjust(2)
    return builder.as_markup()




async def student_slots_keyboard(action: str, student_id: int):
    builder = InlineKeyboardBuilder()

    slots = lesson_db.show_slots_for_students(student_id)
    callback = ""

    for id, weekday, time in slots:
        day = days[weekday]
        if action == "delay_slot":
            callback = SlotCallback(
                action="delay_slot",
                slot_id=id
            )
        elif action == "cancel_slot":
            callback = SlotCallback(
                action="cancel_slot",
                slot_id=id
            )
        builder.button(
            text=f"{day} | {time[:-3]}",
            callback_data= callback
        )

    builder.adjust(1)
    return builder.as_markup()

async def teacher_slot_decision_keyboard(
    student_id: int,
    old_slot_id: int,
    new_slot_id: int
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити",
                    callback_data=TeacherSlotDecisionCallback(
                        action="accept",
                        student_id=student_id,
                        old_slot_id=old_slot_id,
                        new_slot_id=new_slot_id
                    ).pack()
                ),
                InlineKeyboardButton(
                    text="❌ Відхилити",
                    callback_data=TeacherSlotDecisionCallback(
                        action="reject",
                        student_id=student_id,
                        old_slot_id=old_slot_id,
                        new_slot_id=new_slot_id
                    ).pack()
                )
            ]
        ]
    )

def unpaid_lesson_kb(lessons: list[tuple], selected_ids: list[int], price_for_lesson: int) -> InlineKeyboardMarkup:

    keyboard = []



    for lesson in lessons:
        if lesson[5] == 0 and lesson[6] != "canceled":
            lesson_id, lesson_date = lesson[0], lesson[3]
            daytime, time = lesson_date.split(" ")
            year, month, day = daytime.split("-")
            hour,minutes,seconds = time.split(":")
            date_of_lesson_formated = f"{day}.{month}.{year} o {hour}:{minutes}"
            icon = "✅" if lesson_id in selected_ids else "⬜"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{icon} {date_of_lesson_formated} — {price_for_lesson} грн",
                    callback_data=SelectPaymentLesson(
                        lesson_id=lesson_id
                    ).pack()
                )
            ])

    total = len(selected_ids) * price_for_lesson

    keyboard.append([
                InlineKeyboardButton(
                    text=f"💳 Оплатити — {total} грн",
                    callback_data="pay_selected_lessons"
                )
            ])

    keyboard.append([
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data="cancel_lesson_payment"
                )
            ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def one_time_lesson_keyboard(request_id: int, student_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Підтвердити",
        callback_data=OneTimeLessonCallback(
            action="accept",
            request_id=request_id,
            student_id = student_id
        ).pack()
    )

    builder.button(
        text="❌ Відхилити",
        callback_data=OneTimeLessonCallback(
            action="reject",
            request_id=request_id,
            student_id= student_id
        ).pack()
    )

    builder.adjust(2)

    return builder.as_markup()


def lesson_for_admin(lessons, current_date):
    builder_lesson = InlineKeyboardBuilder()


    for lesson in lessons:
        lesson_id, start_time, end_time, is_paid, student_id, student_name = lesson
        start = start_time[11:16]
        end = end_time[11:16]
        builder_lesson.row(
            InlineKeyboardButton(
                text=f"👤 {student_name} • {start}–{end} {'✅' if is_paid else '❌'}",
                callback_data=f"lesson:{lesson_id}:{student_id}"
            )
        )

    today = date.today()

    previous_day = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)

    navigation_buttons = []

    if current_date > today:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"lesson_date:{previous_day.isoformat()}"
            )
        )

    if current_date < today + timedelta(days=7):
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Далі ➡️",
                callback_data=f"lesson_date:{next_date.isoformat()}"
            )
        )

    # Усі navigation buttons кладемо В ОДИН рядок
    if navigation_buttons:
        builder_lesson.row(*navigation_buttons)
    return builder_lesson.as_markup()


def lesson_admin_actions_kb(lesson_id, student_id, lesson_date, is_paid):
    builder = InlineKeyboardBuilder()

    # Оплата
    if not is_paid:
        builder.row(
            InlineKeyboardButton(
                text="💰 Позначити оплаченим",
                callback_data=f"mark_paid:{lesson_id}:{student_id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="✅ Урок оплачено",
                callback_data=f"already_paid:{lesson_id}"
            )
        )

    # Перенесення
    builder.row(
        InlineKeyboardButton(
            text="🔄 Перенести урок",
            callback_data=f"reschedule_admin:{lesson_id}"
        )
    )

    # Скасування
    builder.row(
        InlineKeyboardButton(
            text="❌ Скасувати урок",
            callback_data=f"cancel_admin:{lesson_id}"
        )
    )

    # Профіль
    builder.row(
        InlineKeyboardButton(
            text="👤 Профіль учня",
            callback_data=f"student_{student_id}"
        )
    )

    # Назад
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад до уроків",
            callback_data=f"lesson_date:{lesson_date}"
        )
    )

    builder.adjust(2)
    return builder.as_markup()

def students_for_admin(students, page: int = 0, student_per_page: int = 5):
    builder = InlineKeyboardBuilder()

    start = page * student_per_page
    end = start + student_per_page
    students_for_page = students[start:end]
    for student in students_for_page:
        id,name,username = student
        builder.button(
            text=f"👤 {name} • {username}",
            callback_data=f"student_{id}"
        )
    builder.adjust(1)

    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"students_page_{page - 1}"
            )
        )

    if end < len(students):
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Далі ➡️",
                callback_data=f"students_page_{page + 1}"
            )
        )

    if navigation_buttons:
        builder.row(*navigation_buttons)

    return builder.as_markup()

def confirm_lesson_kb(lesson_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Так, скасувати",
        callback_data=f"confirm_cancel_lesson:{lesson_id}"
    )

    builder.button(
        text="⬅️ Ні, залишити урок",
        callback_data=f"cancel_cancel_lesson:{lesson_id}"
    )

    builder.adjust(2)

    return builder.as_markup()


def get_student_actions_keyboard(student_id):
    builder = InlineKeyboardBuilder()
    username = student_db.get_student(student_id)[2]

    builder.button(
        text="❌Видалити учня",
        callback_data=f"delete_student:{student_id}"
    )
    builder.button(
        text="💸Змінити баланс",
        callback_data=f"change_balance:{student_id}"
    )
    builder.button(
        text="✉️ Написати Учню",
        url=f"https://t.me/{username}"
    )
    builder.button(
        text="⬅️ Назад до учнів",
        callback_data=f"students_page_0"
    )
    builder.adjust(2)

    return builder.as_markup()

def confirm_delete_student(student_id):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Так, видалити",
        callback_data=f"confirm_delete_student:{student_id}"
    )
    builder.button(
        text="❌ Скасувати",
        callback_data=f"student_{student_id}"
    )
    builder.adjust(2)

    return builder.as_markup()

def confirm_change_balance(student_id,balance):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Так змінити баланс",
        callback_data=f"accept_change_balance:{student_id}:{balance}"
    )

    builder.button(
        text="❌ Ні, відмінити операцію",
        callback_data=f"student_{student_id}"
    )

    builder.adjust(2)
    return builder.as_markup()

def show_weekdays():
    builder = InlineKeyboardBuilder()
    for k,v in days.items():
        builder.button(
            text= v,
            callback_data=f"weekday_{k}"
        )

    builder.adjust(1)
    return builder.as_markup()

def accept_new_slot(weekday: int, time: str, duration: int):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Так,створити",
        callback_data=NewSlot(
            weekday=weekday,
            time=time,
            duration=duration
        )
    )

    builder.button(
        text="❌ Ні, змінити дані",
        callback_data="decline_new_slot"
    )

    builder.adjust(2)
    return builder.as_markup()
