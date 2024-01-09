from datetime import timedelta
from decimal import Decimal

from pydantic import Field

from money.account import Account
from money.organization import Organization


class BankAccount(Account):
    bank: Organization
    annual_interest: Decimal = Field(default=Decimal(), decimal_places=2)
    interest_period: timedelta = Field(default_factory=timedelta)
