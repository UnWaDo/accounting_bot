from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.types.callback_query import CallbackQuery

from bot.keyboards.accounts_keyboard import accounts_inline_keyboard
from bot.main_menu import cancel_handler
from bot.utils import collect_object_field
from money.account import Account
from money.transaction import Transaction
from orm.api import add_transactions, get_account_details, get_accounts
from orm.exc import InvalidFieldsError

pass_money_router = Router()


class PassMoneyForm(StatesGroup):
    select_source = State()
    select_target = State()

    set_sum = State()

    set_category = State()
    set_comment = State()

    categories = [
        'Еда',
        'Зарплата',
        'Развлечения',
        'Регулярные платежи',
        'Инвестиции',
    ]


category_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=i) for i in PassMoneyForm.categories]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


@pass_money_router.message(F.text.casefold() == 'pass money')
async def start(message: Message, state: FSMContext):

    await state.set_state(PassMoneyForm.select_source)

    accounts = await get_accounts()
    await message.answer('Select source account',
                         reply_markup=accounts_inline_keyboard(accounts))


@pass_money_router.callback_query(PassMoneyForm.select_source)
async def select_source_account(query: CallbackQuery, state: FSMContext):
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

    source_id = int(query.data)
    source = await get_account_details(source_id, False)

    await state.update_data(source_id=source_id, source=source)
    await state.set_state(PassMoneyForm.select_target)
    await query.message.answer(
        'Now use the same message to select target account')
    await query.answer()


@pass_money_router.callback_query(PassMoneyForm.select_target)
async def select_target_account(query: CallbackQuery, state: FSMContext):
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

    target_id = int(query.data)
    source_id = data['source_id']

    if target_id == source_id:
        await query.answer('Must select different accounts')
        return

    source = data['source']
    target = await get_account_details(target_id, False)

    await state.update_data(target_id=target_id, target=target)
    await state.set_state(PassMoneyForm.set_sum)
    await query.message.edit_text('Accounts selected:'
                                  f' from {source.name} to {target.name}')
    await query.message.answer('Input sum')


@pass_money_router.message(PassMoneyForm.set_sum)
async def set_sum(message: Message, state: FSMContext):
    value = await collect_object_field(
        message,
        state,
        model=Transaction,
        field='value',
    )
    if value is None:
        return

    await state.set_state(PassMoneyForm.set_category)
    await message.answer(
        'Input category or select from the list',
        reply_markup=category_keyboard,
    )


@pass_money_router.message(PassMoneyForm.set_category)
async def set_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)

    await state.set_state(PassMoneyForm.set_comment)
    await message.answer('Input comment')


@pass_money_router.message(PassMoneyForm.set_comment)
async def set_comment(message: Message, state: FSMContext):
    await state.update_data(category=message.text)

    data = await state.get_data()

    source: Account = data['source']
    target: Account = data['target']

    source.pass_money(
        target=target,
        value=data['value'],
    )

    try:
        await add_transactions(source)
        await add_transactions(target)
        text = 'Transaction saved'
    except InvalidFieldsError:
        text = 'Error while saving transaction'

    await cancel_handler(message, state, text)
