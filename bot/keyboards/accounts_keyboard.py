from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from money.account import Account
from orm.api import get_organizations


def accounts_inline_keyboard(accounts: List[Account]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for account in accounts:
        button = InlineKeyboardButton(text=account.name,
                                      callback_data=f'{account.id}')
        keyboard.row(button)

    button = InlineKeyboardButton(text='Cancel', callback_data='cancel')
    keyboard.row(button)

    return keyboard.as_markup()


async def organizations_inline_keyboard():
    organizations = await get_organizations()

    keyboard = InlineKeyboardBuilder()

    for organization in organizations:
        button = InlineKeyboardButton(text=organization.name,
                                      callback_data=f'{organization.id}')
        keyboard.row(button)

    button = InlineKeyboardButton(text='Add new', callback_data='new')
    keyboard.row(button)
    button = InlineKeyboardButton(text='Cancel', callback_data='cancel')
    keyboard.row(button)

    return keyboard.as_markup()
