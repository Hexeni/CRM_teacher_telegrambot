from aiogram.fsm.state import StatesGroup, State


class DeleteAccount(StatesGroup):
    confirmation = State()


class ChangeData(StatesGroup):
    waiting = State()
