import aiogram
import asyncio
from Utilis.Date import Date
from Utilis.reminders import check_reminders
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.lesson_repo import LessonRepo
from aiogram import Bot, Dispatcher
from config import API_KEY
from handlers.base_handlers import router as base_handlers_router
from handlers.registration_handlers import router as registration_handlers_router
from handlers.loging_handlers import router as loging_handlers_router
from handlers.teacher_handlers import router as teacher_handlers_router
from handlers.delay_lesson_handlers import router as delay_lesson_router
from handlers.user_seting_handlers import router as user_settings_router
from handlers.payment_handlers import router as payment_router
from handlers.admin_handlers import router as admin_router


bot = Bot(token=API_KEY)
dp = Dispatcher()
lesson_db = LessonRepo("database/bot_db.db")


async def main():
    dp.include_router(base_handlers_router)
    dp.include_router(registration_handlers_router)
    dp.include_router(loging_handlers_router)
    dp.include_router(teacher_handlers_router)
    dp.include_router(delay_lesson_router)
    dp.include_router(user_settings_router)
    dp.include_router(payment_router)
    dp.include_router(admin_router)

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        check_reminders,
        trigger="interval",
        minutes=1,
        args=[bot,lesson_db]
    )

    scheduler.start()
    print(Date.find_next_weekday(0))
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

