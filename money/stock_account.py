from decimal import Decimal

from pydantic import Field

from money.account import Account
from money.organization import Organization


class StockAccount(Account):
    broker: Organization
    is_iia: bool = False

    stock_value: Decimal = Field(default=0, decimal_places=2)
