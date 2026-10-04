from aiogram.fsm.state import StatesGroup, State

class PaymentState(StatesGroup):
    payment_amount = State()
    sending_to_teacher = State()