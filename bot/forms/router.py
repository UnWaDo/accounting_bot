from aiogram import Router

from bot.forms.add_account import add_account_router
from bot.forms.check_account import check_account_router
from bot.forms.pass_money import pass_money_router

forms_router = Router()
forms_router.include_routers(
    add_account_router,
    check_account_router,
    pass_money_router,
)
