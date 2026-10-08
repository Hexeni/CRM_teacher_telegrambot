from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import teacher_username, support_username
main_rp_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text = "Мій профіль 👤" ),KeyboardButton(text="Мої уроки📅")],
    [KeyboardButton(text="Змніити/перенести урок 📖"), KeyboardButton(text="Налаштування 🕦")]

],resize_keyboard=True,
  input_field_placeholder="оберіть пункт з меню")

phone_number_rp_keyboard = ReplyKeyboardMarkup(keyboard= [[KeyboardButton(text= "Поділитися номером телефона📞", request_contact=True)]],
                                               resize_keyboard=True,
                                               one_time_keyboard=True)

profile_keyboard = InlineKeyboardMarkup(inline_keyboard= [
    [InlineKeyboardButton(text="Поповнити баланс", callback_data="withdraw"), InlineKeyboardButton(text="Додати урок", callback_data="add_lesson")]
])

delay_lesson_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Змінити слот", callback_data="delay_slots"), InlineKeyboardButton(text="📅 Перенести урок",callback_data="delay_lesson")],
[InlineKeyboardButton(text="🗑 Видалити слот", callback_data="reject_slot"), InlineKeyboardButton(text="❌ Скасувати урок", callback_data="cancel_lesson")]
])

settings_user_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text = "Змінити дані профілю 👤"), KeyboardButton(text = "🗑 Видалити акаунт"), KeyboardButton(text = "Звязатися з підтримкою 📨")],
    [KeyboardButton(text= "⬅️ Назад")]
], resize_keyboard=True)

delete_account_confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⚠️ Продовжити видалення", callback_data="continue_delete_account"),
     InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_delete_account")]
])

change_account_info_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Змінити пароль"), KeyboardButton(text = "Змінити логін")],
    [KeyboardButton(text = "⬅️ Назад")]
], resize_keyboard=True)

support_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👨‍🏫 Викладач", url=f"https://t.me/{teacher_username}"),
        InlineKeyboardButton(text="🛠️ Технічна підтримка", url=f"https://t.me/{support_username}")
    ]]
)

accept_user_payment_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text= "✅Я оплатив", callback_data="aprove_payment_user"),
         InlineKeyboardButton(text="❌Скасувати", callback_data="decline_payment_user")]
    ]
)
pay_lesson_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Оплатити урок💵", callback_data="pay_unpaid_lessons")]
    ]
)


admin_keyboard_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚Уроки"), KeyboardButton(text="👨‍🎓Учні")],
        [KeyboardButton(text="🕦Слоти"), KeyboardButton(text="❓Статистика")]
    ], resize_keyboard=True
)

onetime_lesson_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅Так,відправити", callback_data="send_onetimelesson_request"),
            InlineKeyboardButton(text="❌Ні, переробити", callback_data="cancel_onetimelesson_request")
        ]
    ]
)

slots_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Додати новий слот"),KeyboardButton(text="🕦 Подивитися наявні слоти")],
        [KeyboardButton(text="⬅️ Повернутися назад до Панелі")]
    ],resize_keyboard=True
)