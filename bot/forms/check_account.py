import locale
from typing import Union

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.types.callback_query import CallbackQuery

from bot.keyboards.accounts_keyboard import accounts_inline_keyboard
from bot.main_menu import cancel_button, cancel_handler
from bot.utils import DATE_FORMAT, unrecognized_handler
from money.account import Account
from money.bank_account import BankAccount
from money.stock_account import StockAccount
from orm.api import (get_account_details, get_accounts,
                     get_bank_account_details, get_bank_accounts,
                     get_stock_account_details, get_stock_accounts)

check_account_router = Router()


class CheckAccountForm(StatesGroup):
    select_type = State()
    select_account = State()

    allowed_types = ['bank', 'stock', 'all']


account_types_selection = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text=f'{b.capitalize()} accounts')
        for b in CheckAccountForm.allowed_types
    ],
    [cancel_button],
],
                                              resize_keyboard=True)


@check_account_router.message(F.text.casefold() == 'check account')
async def start(message: Message, state: FSMContext):

    await state.set_state(CheckAccountForm.select_type)

    await message.answer('Select account type',
                         reply_markup=account_types_selection)


@check_account_router.message(CheckAccountForm.select_type)
@check_account_router.message(CheckAccountForm.select_account)
async def select_type(message: Message, state: FSMContext):

    account_type = message.text.split()[0].casefold()
    if account_type not in CheckAccountForm.allowed_types:
        return await unrecognized_handler(message)

    if account_type == 'all':
        accounts = await get_accounts()
    elif account_type == 'bank':
        accounts = await get_bank_accounts()
    elif account_type == 'stock':
        accounts = await get_stock_accounts()
    else:
        accounts = []

    if not accounts:
        await message.answer('No accounts of this type')
        return

    await state.update_data(account_type=account_type, message_id=None)
    await state.set_state(CheckAccountForm.select_account)

    await message.answer(
        'Select account',
        reply_markup=accounts_inline_keyboard(accounts),
    )


def describe_account(
        account: Union[Account, BankAccount, StockAccount]) -> str:
    account_description = (
        f'Name: {account.name}\n'
        f'Code: {account.code}\n'
        f'Was opened at {account.start_date.strftime(DATE_FORMAT)}'
        f' with balance {locale.currency(account.start_balance)}\n'
        f'Current balance is: {locale.currency(account.get_balance())}')

    if isinstance(account, BankAccount):
        bank = account.bank
        bank_description = (f'The bank is {bank.name}')

        return f'{account_description}\n\n{bank_description}'

    elif isinstance(account, StockAccount):
        broker = account.broker
        broker_description = (f'The broker is {broker.name}')

        return f'{account_description}\n\n{broker_description}'

    return account_description


@check_account_router.callback_query(CheckAccountForm.select_account)
async def select_account(query: CallbackQuery, state: FSMContext):
    if query.data is None:
        await query.answer('This message is outdated')
        return
    if query.data == 'cancel':
        await query.answer('Cancelling')
        await cancel_handler(query.message, state)
        return
    if not query.data.isnumeric():
        await query.answer('Invalid callback')
        return

    data = await state.get_data()

    account_id = int(query.data)
    account_type = data['account_type']

    if account_type == 'all':
        account = await get_account_details(account_id)
    elif account_type == 'bank':
        account = await get_bank_account_details(account_id)
    elif account_type == 'stock':
        account = await get_stock_account_details(account_id)
    else:
        return await query.answer('Not supported yet')

    if account is None:
        return await query.answer('No such account')

    text = describe_account(account)

    message_id = data.get('message_id')
    if message_id is not None:
        try:
            result = await query.bot.edit_message_text(text,
                                                       query.message.chat.id,
                                                       message_id)
        except TelegramBadRequest as e:
            if 'exactly the same' in e.message:
                return await query.answer()
            message = await query.message.answer(text)
            await state.update_data(message_id=message.message_id)
    else:
        message = await query.message.answer(text)
        await state.update_data(message_id=message.message_id)
    await query.answer()
