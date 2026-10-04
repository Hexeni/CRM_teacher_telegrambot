import asyncio
from keyboards.keyboards import pay_lesson_kb

async def check_reminders(bot, lesson_db):
    print("Надіслано")
    for hour in (24,4,1):
        lessons = lesson_db.get_lessons_for_reminder(hour)
        for lesson in lessons:
            lesson_id, account_id, start_time, is_paid = lesson

            if is_paid:
                payment_text = "✅ Урок оплачений, все добре!"
                keyboard = None
            else:
                payment_text = (
                    "⚠️ Урок ще не оплачений.\n"
                    "Будь ласка, не забудьте оплатити його до початку."

                )
                keyboard = pay_lesson_kb

            try:
                if hour == 1 and not is_paid:
                    text_to_send = "нажаль не вдалося отримати оплату вчасно, урок скасовнаий :("
                    lesson_db.cancel_lesson(lesson_id)
                    keyboard = None
                else:
                    text_to_send = (
                        f"⏰ Нагадування про урок!\n\n"
                        f"Урок почнеться через {hour} год.\n"
                        f"🕐 {start_time}\n\n"
                        f"{payment_text}"
                    )

                await bot.send_message(
                    chat_id=account_id,
                    text=text_to_send,
                    reply_markup=keyboard
                )

                print(
                     f"Нагадуваня для користувача надіслано за {hour}"
                )

                lesson_db.mark_reminder_as_sent(lesson_id, hour)

            except Exception as e:
                print(
                    f"Помилка reminder для lesson {lesson_id}: {e}"
                )



