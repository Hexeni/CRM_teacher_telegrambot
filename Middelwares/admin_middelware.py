from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable
from aiogram.types import(
    CallbackQuery,
    Message,
    TelegramObject
)
from config import id_admin, id_teacher

class AdminMiddleware(BaseMiddleware):

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

        if user is None:
            return

        allowed_ids = (id_admin, id_teacher)

        if user.id not in allowed_ids:
            if isinstance(event, Message):
                await event.answer(
                    "⛔ У вас немає прав для цієї дії."
                )

            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⛔ Доступ заборонено.",
                    show_alert=True
                )

            return
        return await handler(event, data)