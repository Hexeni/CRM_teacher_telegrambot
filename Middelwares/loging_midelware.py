from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable
from database.student_repo import StudentRepo
from aiogram.types import(
    CallbackQuery,
    Message,
    TelegramObject
)
from config import id_admin, id_teacher

class UserLogingMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any]
        ],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")

        student_db = StudentRepo("database/bot_db.db")

        student_info = student_db.get_student(user.id)
        if student_info is None:
            return await handler(event, data)

        is_loged = student_info[9]

        if not is_loged:
            if isinstance(event, Message):
                await event.answer(
                    "⛔ У вас немає прав для цієї дії, спочатку увійдіть в свій аккаунт командою /log"
                )

            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⛔ Доступ заборонено.",
                    show_alert=True
                )

            return
        return await handler(event, data)