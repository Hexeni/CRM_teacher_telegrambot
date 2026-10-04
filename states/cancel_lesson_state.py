from aiogram.fsm.state import StatesGroup, State

class Cancel(StatesGroup):
    reason = State()