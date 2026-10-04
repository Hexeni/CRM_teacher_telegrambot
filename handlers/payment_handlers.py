from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states.payment_state import PaymentState
from Utilis.Validator import Validator
from config import CARD_NUMBER, id_teacher
from keyboards.techer_keyboard import payment_teacher_kb
from keyboards.keyboards import accept_user_payment_kb
from keyboards.keyboards_builder import SelectPaymentLesson, unpaid_lesson_kb
from handlers.base_handlers import student_db, lesson_db
router = Router()

@router.callback_query(F.data == "withdraw")
async def payment_process_beginning( callback: CallbackQuery, state: FSMContext):
    pendings = student_db.show_pending_payments(callback.from_user.id)
    if not pendings:
        await callback.message.answer("""
        💳 Введіть суму поповнення у гривнях (лише число, без коми та крапки).
    Наприклад: 300 — для поповнення на 300 грн
        """)
        await state.set_state(PaymentState.payment_amount)
    else:
        await callback.message.answer(
            "⏳ У вас уже є платіж, який очікує підтвердження.\n\n"
            "Дочекайтеся відповіді викладача перед створенням нового запиту."
        )


@router.message(PaymentState.payment_amount)
async def checking_amount(message: Message, state: FSMContext):
    payment_amount = message.text.strip()
    await state.update_data(amount = payment_amount)
    if Validator.check_payment_amount(payment_amount):
        await message.answer(f"""
        💳 <b>Оплата</b>

Перекажіть кошти на картку:

<code>{CARD_NUMBER}</code>

Сума до сплати: <b>{payment_amount} грн</b>

Після оплати натисніть кнопку «Я оплатив».
        """, parse_mode="html", reply_markup=accept_user_payment_kb)

    else:
        await message.answer("""
        ❌ <b>Некоректний формат суми</b>

Введіть суму лише цифрами, без пробілів, коми, крапки та позначення валюти.

Наприклад: <code>300</code>
        """, parse_mode="html")


@router.callback_query(F.data == "aprove_payment_user")
async def aprove_payment_user(callback: CallbackQuery, state: FSMContext):
    student_id = callback.from_user.id
    amount = await state.get_value("amount")
    if student_db.pending_payment(student_id, amount):
        await callback.message.answer(
            f"""
        💳 <b>Оплату надіслано на підтвердження</b>

        Сума: <b>{amount} грн</b>

        👩‍🏫 Вчитель отримав ваш запит і має підтвердити оплату.

    Після підтвердження кошти автоматично будуть зараховані на ваш баланс. ✅
        """,
            parse_mode="HTML"

        )
        student_name = student_db.get_student(student_id)[2]
        print(student_name)
        await callback.bot.send_message(id_teacher, text=f"""
        💰 <b>Нове підтвердження оплати</b>

👤 Учень: <b>{student_name}</b>
💵 Сума: <b>{amount} грн</b>

Учень повідомив про здійснення оплати.
Підтвердіть її отримання 👇
        """, reply_markup= payment_teacher_kb(student_id), parse_mode="HTML")

    else:
        await callback.message.answer("""
        На жаль сталася якась помилка, напишіть адміну щоб вирішити її
        """)
    await state.clear()
@router.callback_query(F.data == "decline_payment_user")
async def decline_user_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.edit_text(
        "❌ Поповнення балансу скасовано."
    )

    await callback.answer()


@router.callback_query(SelectPaymentLesson.filter())
async def select_lesson_for_payment(
    callback: CallbackQuery,
    callback_data: SelectPaymentLesson,
    state: FSMContext
):
    lesson_id = callback_data.lesson_id
    telegram_id = callback.from_user.id
    price = student_db.get_student(telegram_id)[7]

    data = await state.get_data()

    selected_ids = data.get("selected_lesson_ids", [])
    lessons = data.get("unpaid_lessons", [])

    if lesson_id in selected_ids:
        selected_ids.remove(lesson_id)
    else:
        selected_ids.append(lesson_id)

    await state.update_data(
        selected_lesson_ids=selected_ids
    )

    await callback.message.edit_reply_markup(
        reply_markup=unpaid_lesson_kb(
            lessons=lessons,
            selected_ids=selected_ids,
            price_for_lesson= price
        )
    )

    await callback.answer()

@router.callback_query(F.data == "pay_unpaid_lessons")
async def show_unpaid_lessons(
        callback: CallbackQuery,
        state: FSMContext
):

    lessons = lesson_db.show_lesson_for_student(callback.from_user.id)
    unpaid_lessons = [lesson for lesson in  lessons if lesson[5] == 0]
    if unpaid_lessons:
        price = student_db.get_student(callback.from_user.id)[7]
        balance = student_db.get_student(callback.from_user.id)[8]

        await state.update_data(
            unpaid_lessons = unpaid_lessons,
            selected_lesson_ids = []
        )

        print("ALL LESSONS:", lessons)
        print("UNPAID LESSONS:", unpaid_lessons)
        print("UNPAID COUNT:", len(unpaid_lessons))

        await callback.message.answer(
            f"📚 Оберіть уроки, які хочете оплатити:\n💸 Ваш баланс: <b>{balance} грн</b>",
            parse_mode= "HTML",
            reply_markup=unpaid_lesson_kb(
                lessons=unpaid_lessons,
                selected_ids=[],
                price_for_lesson=price

            )
        )

    else:
        await callback.message.answer(
            "Всі уроки оплачені😊"
        )

    await callback.answer()

@router.callback_query(F.data == "pay_selected_lessons")
async def pay_selected_lessons(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    selected_ids = data.get("selected_lesson_ids", [])
    unpaid_lessons = data.get("unpaid_lessons", [])

    if not selected_ids:
        await callback.answer(
            "Оберіть хоча б один урок",
            show_alert=True
        )
        return

    price = student_db.get_student(callback.from_user.id)[7]
    total_amount = len(selected_ids) * price

    if student_db.pay_for_lesson(selected_ids, total_amount, callback.from_user.id):
        await callback.message.edit_text("""
        Супер, ваші уроки сплачені
        """)

    else:
        await callback.message.edit_text("""
                Нажаль сталася помилка, перевірте чи достатньо коштів у вас на балансі або зверніться до тех підтримки
                """)

