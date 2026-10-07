from aiogram import F, Router
from aiogram.types import  Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states.DeleteAccount import DeleteAccount
from keyboards.keyboards import main_rp_keyboard
from handlers.base_handlers import student_db
from states.DeleteAccount import ChangeData
from config import id_admin, id_teacher
from Utilis.Validator import Validator
from keyboards.techer_keyboard import password_change_admin_keyboard


router = Router()


@router.callback_query(F.data == "continue_delete_account")
async def proof_account_delete(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteAccount.confirmation)

    await callback.message.edit_text(
        "🚨 <b>Останнє підтвердження</b>\n\n"
        "Для остаточного видалення акаунту введіть слово:\n\n"
        "<code>ВИДАЛИТИ</code>\n\n"
        "Для скасування напишіть <code>СКАСУВАТИ</code>.",
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "cancel_delete_account")
async def cancel_delete_account(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.clear()

    await callback.message.edit_text(
        "✅ Видалення акаунту скасовано.\n\n"
        "Ваш профіль і всі дані залишилися без змін."
    )

    await callback.answer("Операцію скасовано")

@router.message(DeleteAccount.confirmation)
async def confirm_delete_account(message: Message, state: FSMContext):
    confirmation = message.text.strip().upper()

    if confirmation == "СКАСУВАТИ":
        await state.clear()

        await message.answer("""
        ✅ Видалення акаунту скасовано
        Ваші дані залишилися без змін
        """, reply_markup=main_rp_keyboard)
        return

    if confirmation != "ВИДАЛИТИ":
        await message.answer(
            "❌ Підтвердження не розпізнано.\n\n"
            "Для видалення введіть точно:\n"
            "<code>ВИДАЛИТИ</code>\n\n"
            "Для скасування введіть:\n"
            "<code>СКАСУВАТИ</code>",
            parse_mode="HTML"
        )
        return

    user_id = message.from_user.id

    deleted = student_db.delete_user_info(user_id)

    if deleted:
        await state.clear()

        await message.answer(
            "✅ <b>Ваш акаунт успішно видалено</b>\n\n"
            "Усі пов’язані з ним дані були видалені із системи.\n\n"
            "Дякуємо, що користувалися нашим ботом.",
            parse_mode="HTML",
        )

        await message.bot.send_message(
            chat_id=525989603,
            text=(
                "🗑 Користувач видалив акаунт\n\n"
                f"Telegram ID: <code>{user_id}</code>"
            ),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Під час видалення акаунту сталася помилка.\n\n"
            "Ваші дані не були видалені. Спробуйте пізніше "
            "або зверніться до викладача."
        )

@router.message(F.text.in_(
    {
        "Змінити логін",
        "Змінити пароль"
    }
))
async def start_changing_account_data(message: Message, state: FSMContext):
    if student_db.check_if_logged(message.from_user.id):
        if message.text == "Змінити логін":
            field = "login"
            text = ("👤 <b>Зміна логіна</b>\n\n"
                "Введіть новий логін:")

        else:
            field = "password"
            text = (
                "🔐 <b>Зміна пароля</b>\n\n"
                "Введіть новий пароль:"
            )
        await state.update_data(field=field)
        await state.set_state(ChangeData.waiting)

        await message.answer(
            text,
            parse_mode="HTML"
        )
    else:
        await message.answer("Для початку увійдйть в свій аккаунт")

@router.message(ChangeData.waiting)
async def sending_new_account_data(message: Message, state: FSMContext):
    field = await state.get_value("field")
    if field == "password":
        password = message.text.strip()
        if Validator.validate_password(password):
            hash_pass = Validator.make_hash(password)
            request_id = (
                student_db.create_password_change_request(
                    telegram_id=message.from_user.id,
                    new_password=hash_pass
                )
            )
            if request_id is None:
                await message.answer(
                    "❌ <b>Не вдалося створити запит</b>\n\n"
                    "Ваш акаунт не знайдено або сталася "
                    "помилка під час збереження запиту.",
                    parse_mode="HTML"
                )
                return
            await state.update_data(password=hash_pass)
            username = student_db.get_student(message.from_user.id)[2]
            await message.bot.send_message(chat_id=id_admin, text=f"""
            Учень {username} хоче змінити пароль
            Ви підтверджуєте це??
            """, reply_markup=password_change_admin_keyboard(request_id))
            await message.answer("Ми відправили заявку адміну, очікуйте на відповідь")
            await state.clear()
        else:
            await message.answer("Нажаль пароль не відповідає вимогам повторіть ще раз")

    elif field == "login":
        new_login = message.text.strip()
        user_id = message.from_user.id
        old_name = student_db.show_profile_data(user_id)[0]
        change = student_db.change_name_profile(user_id, new_login)
        if change:
            await message.answer("Супер, ваш логін був оновлений")
            await message.bot.send_message(id_teacher, text=f"""
            Користувач {old_name} змінив своє ім'я на {new_login}
            """)
        else:
            await message.answer("""
            Нажаль щось пішло не так, спробуйте пізніше або напишіть в тех підтримку
            """)

