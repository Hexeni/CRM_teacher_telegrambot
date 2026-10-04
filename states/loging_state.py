from aiogram.fsm.state import StatesGroup, State

class Log(StatesGroup):
    password = State()

class AddOneTimelesson(StatesGroup):
    waiting_for_date = State()