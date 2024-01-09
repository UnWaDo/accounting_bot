from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from aiogram.types.callback_query import CallbackQuery
from pydantic import ValidationError

from bot.keyboards.accounts_keyboard import organizations_inline_keyboard
from bot.main_menu import cancel_handler
from bot.utils import collect_object_field, collect_value, is_in_list
from money.account import Account
from money.bank_account import BankAccount
from money.organization import Organization
from money.stock_account import StockAccount
from orm.api import create_account, get_organization
from orm.exc import InvalidFieldsError

add_account_router = Router()


class AddAccountForm(StatesGroup):
    set_name = State()
    set_code = State()
    set_balance = State()
    select_type = State()

    select_org = State()
    new_org_name = State()
    new_org_shortcut = State()

    allowed_types = ['bank', 'stock', 'simple']


select_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[[
        KeyboardButton(text=f'{b.capitalize()} account')
        for b in AddAccountForm.allowed_types
    ]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


@add_account_router.message(F.text.casefold() == 'add account')
async def start(message: Message, state: FSMContext):

    await state.set_state(AddAccountForm.set_name)

    await message.answer('Input name for a new account',
                         reply_markup=ReplyKeyboardRemove())


@add_account_router.message(AddAccountForm.set_name)
async def set_name(message: Message, state: FSMContext):
    value = await collect_object_field(
        message,
        state,
        model=Account,
        field='name',
    )
    if value is None:
        return

    await state.set_state(AddAccountForm.set_code)
    await message.answer('Input code for a new account')


@add_account_router.message(AddAccountForm.set_code)
async def set_code(message: Message, state: FSMContext):
    value = await collect_object_field(
        message,
        state,
        model=Account,
        field='code',
    )
    if value is None:
        return

    await state.set_state(AddAccountForm.set_balance)
    await message.answer('Input starting balance')


@add_account_router.message(AddAccountForm.set_balance)
async def set_balance(message: Message, state: FSMContext):
    value = await collect_object_field(
        message,
        state,
        model=Account,
        field='start_balance',
    )
    if value is None:
        return

    await state.set_state(AddAccountForm.select_type)
    await message.answer('Select type for a new account',
                         reply_markup=select_type_keyboard)


@add_account_router.message(AddAccountForm.select_type)
async def select_type(message: Message, state: FSMContext):

    account_type = await collect_value(
        message,
        state,
        validator=lambda x: (is_in_list(x, AddAccountForm.allowed_types)),
        parser=lambda x: x.split()[0].casefold(),
    )

    if account_type == 'simple':
        await validate(message, state)
        return

    if account_type == 'bank':
        org_name = 'bank'
    elif account_type == 'stock':
        org_name = 'broker'

    await state.update_data(account_type=account_type)

    await state.set_state(AddAccountForm.select_org)
    await message.answer(f'Select {org_name} for the account',
                         reply_markup=await organizations_inline_keyboard())


@add_account_router.callback_query(AddAccountForm.select_org)
async def select_org(query: CallbackQuery, state: FSMContext):
    if query.data is None:
        await query.answer('This message is outdated')
        return

    if query.data == 'cancel':
        await query.answer('Cancelling')
        await cancel_handler(query.message, state)
        return

    if query.data == 'new':
        await query.answer('Will create new organization')
        await state.set_state(AddAccountForm.new_org_name)
        await query.message.answer('Input name for a organization')
        return

    if not query.data.isnumeric():
        await query.answer('Invalid callback')
        return

    org = await get_organization(int(query.data))
    if org is None:
        return await query.answer('No such organization')

    await state.update_data(org=org.model_dump())
    await query.answer()
    await validate(query.message, state)


@add_account_router.message(AddAccountForm.new_org_name)
async def new_org_name(message: Message, state: FSMContext):
    value = await collect_object_field(
        message,
        state,
        model=Organization,
        field='name',
        dict_name='org',
    )
    if value is None:
        return

    await state.set_state(AddAccountForm.new_org_shortcut)
    await message.answer('Input shortcut for an organization')


@add_account_router.message(AddAccountForm.new_org_shortcut)
async def new_org_shortcut(message: Message, state: FSMContext):
    value = await collect_object_field(
        message,
        state,
        model=Organization,
        field='shortcut',
        dict_name='org',
    )
    if value is None:
        return

    await validate(message, state)


async def validate(message: Message, state: FSMContext):
    data = await state.get_data()

    try:
        if 'org' not in data:
            account = Account.model_validate(data)
        elif data['account_type'] == 'bank':
            data['bank'] = data['org']
            account = BankAccount.model_validate(data)
        else:
            data['broker'] = data['org']
            account = StockAccount.model_validate(data)

    except ValidationError as e:
        text = 'Invalid data. Try again from the beginning'
        await cancel_handler(message, state, text)
        return

    try:
        await create_account(account)
        text = 'New account created'
    except InvalidFieldsError as e:
        if e.fields[0][0] == 'name':
            additional = ''
            if 'bank' in data:
                additional = 'or bank '
            elif 'broker' in data:
                additional = 'or broker '

            text = f'Account {additional}with such name already exists'
        else:
            e.fields[0][0] == 'code'
            text = 'Account with such code already exists'
    await cancel_handler(message, state, text)
