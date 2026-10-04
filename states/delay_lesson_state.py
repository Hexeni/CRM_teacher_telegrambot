from aiogram.fsm.state import StatesGroup, State


class Delay(StatesGroup):
    waiting = State()
    sending = State()


class RejectDelay(StatesGroup):
    waiting_reason = State()
