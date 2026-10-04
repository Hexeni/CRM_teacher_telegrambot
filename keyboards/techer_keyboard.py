from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData


class PasswordChangeCallback(
    CallbackData,
    prefix="password_change"
):
    action: str
    request_id: int


class AcceptPaymentTeacher(
    CallbackData,
    prefix="accept_teacher_payment"
):
    action: str
    student_id: int


slot_keyboard = InlineKeyboardMarkup(inline_keyboard= [
    [InlineKeyboardButton(text="Прийняти", callback_data= "accept_slot"), InlineKeyboardButton(text="Відхилити", callback_data="refuse_slot")]
])

def password_change_admin_keyboard(
    request_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити",
                    callback_data=PasswordChangeCallback(
                        action="accept",
                        request_id=request_id
                    ).pack()
                ),
                InlineKeyboardButton(
                    text="❌ Відхилити",
                    callback_data=PasswordChangeCallback(
                        action="reject",
                        request_id=request_id
                    ).pack()
                )
            ]
        ]
    )

def payment_teacher_kb(
        student_id: int
)-> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard= [
            [InlineKeyboardButton(text="Aprove✅", callback_data=AcceptPaymentTeacher(student_id= student_id, action= "accept").pack()),
             InlineKeyboardButton(text="Decline❌", callback_data=AcceptPaymentTeacher(student_id=student_id, action= "reject").pack())]
        ]
    )