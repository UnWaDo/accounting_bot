from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Check account')],
        [KeyboardButton(text='Add account')],
        [KeyboardButton(text='Pass money')],
        # [KeyboardButton(text='Help')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)
cancel_button = KeyboardButton(text='Go to menu')


async def cancel_handler(message: Message,
                         state: FSMContext,
                         text: str = None):
    await state.clear()

    if text is not None:
        await message.answer(f'{text}. Returning to main menu',
                             reply_markup=main_keyboard)
    else:
        await message.answer('Returning to main menu',
                             reply_markup=main_keyboard)
