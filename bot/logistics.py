from aiogram import Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.forms.router import forms_router
from bot.main_menu import cancel_button, cancel_handler, main_keyboard
from bot.utils import unrecognized_handler, unrecognized_callback

USER_ID = 397871650

dispatcher = Dispatcher()

general_router = Router()
general_router.message.register(cancel_handler, Command('cancel'))
general_router.message.register(
    cancel_handler,
    F.text.casefold() == cancel_button.text.casefold())

terminating_router = Router()
terminating_router.message.register(unrecognized_handler)
terminating_router.callback_query.register(unrecognized_callback)

dispatcher.include_router(general_router)
dispatcher.include_router(forms_router)
dispatcher.include_router(terminating_router)


@dispatcher.message(F.from_user.id != USER_ID)
async def invalid_user_handler(message: Message):
    await message.answer('You are not allowed to write here')


@general_router.message(CommandStart())
async def command_start(message: Message):
    await message.reply(f'Hello {message.from_user.full_name}!',
                        reply_markup=main_keyboard)
