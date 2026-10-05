from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from keyboards.keyboards import main_rp_keyboard, phone_number_rp_keyboard
from database.student_repo import StudentRepo
from aiogram.fsm.context import FSMContext
from states.registration_state import Reg
from email_validator import validate_email, EmailNotValidError
from Utilis.Validator import Validator
from keyboards.registration_keyboard import registration

router = Router()
student_db = StudentRepo("database/bot_db.db")

@router.message(Command('reg'))
async def name_reg(message: Message, state:FSMContext):
    if not student_db.get_student(message.from_user.id):
        await state.set_state(Reg.name)
        await message.answer("Для початку введи своє прізвище та імя:")
    else:
        await state.clear()
        await message.answer("Схоже ви вже зареєстрвоані в системі, щоб увійти в свій аккаунт нажміть на мій Профіль")

@router.message(Reg.name)
async def name_reg(message: Message, state:FSMContext):
    await state.update_data(name = message.text)
    await state.set_state(Reg.phone_number)
    await message.answer("Будь ласка натисніть на кнопку щоб поділитися номером телефону", reply_markup= phone_number_rp_keyboard)

@router.message(Reg.phone_number)
async def phone_reg(message: Message, state: FSMContext):
    await state.update_data(phone_number = message.contact.phone_number)
    await state.set_state(Reg.email)
    await message.answer("Будь ласка введи свій імейл:")

@router.message(Reg.email)
async def mail_reg(message: Message, state: FSMContext):
    email = message.text.strip()
    try:
        valid = validate_email(email)
        await state.update_data(email = valid.normalized)
        await state.set_state(Reg.password)
        await message.answer("А тепер введи пароль який буде що найменше складатися з 8 символів, буже напсианий англійською матиме \n хочаби одну цифру та один спецзнак")
    except EmailNotValidError:
        await message.answer("Схоже ти зробив помилку в напсианні імейла спробуй знову, або обери інший")

@router.message(Reg.password)
async def password_reg(message: Message, state: FSMContext):
    password = message.text.strip()
    if Validator.validate_password(password):
        await state.update_data(password = password, telegr_id = message.from_user.id, nickname = message.from_user.username)
        data = await state.get_data()
        await message.answer(f"""
Супер, процес реєстрації майже закінчився,
перевір чи всі введені тобою дані правильні, і якщо так натисни кнопку підтвердити
якщо ж ти хочеш поміняти певні данні то нажми на кнопку почати знову після чого 
процес реєстрації почнеться з початку
Твої данні:
- ім'я та прізвище: {data.get("name")}
- номер телефону: {data.get("phone_number")}
- імейл: {data.get("email")}
- пароль: {data.get("password")}
        """, reply_markup=registration)
    else:
        await message.answer("Схоже ти вписав не парвильний пароль спробуй знову")

@router.callback_query(F.data == "accept_registration")
async def callback_accept(callback: CallbackQuery, state: FSMContext):
    student_db.add_student(await state.get_data())
    await state.clear()
    await callback.message.reply("Супер реєстрація пройшла успішно тепер щоб увійти в свій аакаут натисни на кнопку мій профіль та дотримуйся інструкцій", reply_markup=main_rp_keyboard)

@router.callback_query(F.data == 'refuse_registration')
async def callback_refuse(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Reg.name)
    await callback.message.answer(
        "Для початку введи своє прізвище та ім'я:"
    )

    await callback.answer()






