from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.keyboards import main_rp_keyboard, profile_keyboard, delay_lesson_kb, settings_user_keyboard, \
    delete_account_confirm_kb, change_account_info_kb, support_kb, pay_lesson_kb
from database.student_repo import StudentRepo
from database.lesson_repo import LessonRepo
from datetime import datetime
from Middelwares.loging_midelware import UserLogingMiddleware

router = Router()
router.message.middleware(UserLogingMiddleware())
router.callback_query.middleware(UserLogingMiddleware())

student_db = StudentRepo("database/bot_db.db")
lesson_db = LessonRepo("database/bot_db.db")


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("""
    Привіт! 👋

Ласкаво просимо до системи керування уроками англійської 🇬🇧

Тут ти можеш:
📅 переглядати та планувати уроки  
🔄 переносити заняття  
💰 контролювати баланс та оплату  
👤 керувати своїм профілем  

Почнемо? Обери дію нижче ⬇️
    
    """, reply_markup=main_rp_keyboard)


@router.message(F.text == 'Мій профіль 👤')
async def view_my_profile(message: Message):
    print(message.from_user.id)
    lesson_db.adding_new_lessons_automatically()
    if student_db.get_student(message.from_user.id):
        student_db.logout_inactive_users()
        if student_db.check_if_logged(message.from_user.id):
            student_db.update_activity(message.from_user.id)
            data_student = student_db.show_profile_data(message.from_user.id)
            data_lessons = lesson_db.show_lesson_for_student(message.from_user.id)
            future_lessons = [l for l in data_lessons if l[-1] != 1]

            if future_lessons:
                latest_lesson = min(
                    future_lessons,
                    key=lambda l: l[3]
                )[3]

                dt = datetime.strptime(latest_lesson, "%Y-%m-%d %H:%M:%S")
                pretty = dt.strftime("%d.%m.%Y o %H:%M")
            else:
                pretty = "Немає запланованих уроків"
            dt_last_time = datetime.strptime(data_student[3], "%Y-%m-%d %H:%M:%S")
            pretty_last_time = dt_last_time.strftime("%d.%m.%Y o %H:%M")
            await message.answer(f"""
👤 Ваш профіль

Ім'я:    {data_student[0]}
📧 Email:   {data_student[2]}
📱 Телефон:   {data_student[1]}

─────────────── 
🕒 Останній вхід:  {pretty_last_time}
💰 Баланс:    {data_student[4]}
─────────────── 

📅 Наступний урок
{pretty}           
            """, reply_markup=profile_keyboard)
        else:
            await message.answer(
                "Я бачу що ви зареєстрованій в нашій системі проте вам потрібно увійти в свій аккаунт \n використайте команду /log для цього")

    else:
        await message.answer("""
    Схоже ти ще не зареєстрований в системі 
давай це виправим, напиши команду /reg щоб почати процес реєстрації
        """)


@router.message(F.text == 'Мої уроки📅')
async def show_students_lessons(message: Message):
    lesson_message = "📚 <b>Твої уроки:</b>\n\n"
    lessons = lesson_db.show_lesson_for_student(message.from_user.id)
    if lessons:
        sorted_lessons = sorted(lessons, key=lambda lesson: lesson[3])
        number = 1
        for lesson in sorted_lessons:
            restricted_status = ("canceled", "pending_one_time_lesson", "reject_onetime_lesson")
            if lesson[7] != 1 and lesson[6] not in restricted_status:
                year, month, rest = lesson[3].split("-")
                day, time = rest.split(" ")

                formatted = (
                    f"{number}. 📅 <b>{day}.{month}.{year}</b> о <b>{time[:5]}</b> статус: {"не оплачений 🔴" if lesson[5] == 0 else "оплачений 🟢"}\n"
                    f"   🇺🇦 За Київським часом\n\n"
                )
                lesson_message += formatted
                number += 1

        await message.answer(lesson_message, parse_mode="HTML", reply_markup=pay_lesson_kb)
    else:
        await message.answer(
            "😔 Наразі для вас ще не заплановано жодного уроку.\n\n"
            "Перейдіть у «Мій профіль» і додайте постійний слот, після чого уроки будуть автоматично створені."
        )


@router.message(F.text == "Змніити/перенести урок 📖")
async def delay_lesson(message: Message):
    user_id = message.from_user.id
    lessons = lesson_db.show_lesson_for_student(user_id)
    if lessons:
        await message.answer("""
    Оберіть, що саме ви хочете зробити:
    
    1️⃣ Перенести урок (одноразово)  
    — змінити дату тільки цього уроку
    
    2️⃣ Змінити слот уроку  
    — змінити постійний час занять
        """, reply_markup=delay_lesson_kb)
    else:
        await message.answer(
            "❌ У вас наразі немає активних слотів.\n\n"
            "Спочатку перейдіть у розділ «Мій профіль» та оберіть один із вільних слотів.\n"
            "Після цього ви зможете переносити, змінювати або відміняти свої уроки."
            ,
            show_alert=True
        )
        return


@router.message(F.text == "Налаштування 🕦")
async def settings(message: Message):
    await message.answer(" ⚙️ Оберіть потрібне налаштування:", reply_markup=settings_user_keyboard)


@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):
    await message.answer(
        "🏠 Головне меню",
        reply_markup=main_rp_keyboard
    )


@router.message(F.text == "🗑 Видалити акаунт")
async def delete_account_request(message: Message):
    if student_db.check_if_logged(message.from_user.id):
        data = student_db.show_profile_data(message.from_user.id)
        if data:
            await message.answer(
                "⚠️ <b>Видалення акаунту</b>\n\n"
                "Ви збираєтеся повністю видалити свій акаунт із системи.\n\n"
                "Після видалення буде втрачено:\n"
                "• дані вашого профілю;\n"
                "• активний постійний слот;\n"
                "• усі майбутні уроки;\n"
                "• історію перенесень і скасувань;\n"
                "• інформацію про баланс та оплату.\n\n"
                "❗ Цю дію неможливо буде скасувати.",
                reply_markup=delete_account_confirm_kb,
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "⚠️ <b>Операцію не вдалося виконати</b>\n\n"
                "Ваш акаунт відсутній у системі.\n"
                "Будь ласка, перевірте, чи ви зареєстровані, або зверніться до викладача.",
                parse_mode="HTML"
            )
    else:
        await message.answer("Спочатку увійдіть в свій аакаунт")


@router.message(F.text == "Змінити дані профілю 👤")
async def change_profile_data(message: Message):
    await message.answer("""
        ⚙️ Оберіть потрібне налаштування:
    """, reply_markup=change_account_info_kb)


@router.message(F.text == "Звязатися з підтримкою 📨")
async def support(message: Message):
    await message.answer("""
    🛟 <b>Центр підтримки</b>

Якщо у вас виникли будь-які труднощі або запитання, ми завжди готові допомогти.

Оберіть потрібний розділ:

📚 <b>Питання щодо навчання</b>
Натисніть кнопку <b>«Викладач»</b>, якщо ваше питання стосується:
• розкладу занять;
• перенесення або скасування уроків;
• навчального процесу;
• домашніх завдань;
• будь-яких інших питань до викладача.

⚙️ <b>Технічна підтримка</b>
Натисніть кнопку <b>«Технічна підтримка»</b>, якщо:
• бот працює некоректно;
• виникла помилка під час використання;
• не працюють кнопки або функції;
• є пропозиції щодо покращення бота.

👇 Оберіть потрібний варіант нижче.
    """, parse_mode="HTML", reply_markup=support_kb)


@router.message(F.sticker)
async def get_sticker_id(message: Message):
    await message.answer(
        f"Sticker file_id:\n<code>{message.sticker.file_id}</code>",
        parse_mode="HTML"
    )
