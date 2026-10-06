from aiogram.fsm.state import State, StatesGroup

class AdminState(StatesGroup):
    password = State()

class ChangeBalanceState(StatesGroup):
    new_balance = State()

class NewSlotState(StatesGroup):
    new_hour = State()
    new_duration = State()

