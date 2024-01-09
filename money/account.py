from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from money.transaction import Transaction
from money.utils import moscow_now


class Account(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    id: Optional[int] = None

    name: str = Field(max_length=50)
    code: str = Field(max_length=20)

    start_date: AwareDatetime = Field(default_factory=moscow_now)
    start_balance: Decimal = Field(default=Decimal(), decimal_places=2)

    transactions: List[Transaction] = []

    def __eq__(self, other):
        if isinstance(other, int):
            code = self.code.casefold()
            return code == str(other).casefold()
        if isinstance(other, str):
            name = self.name.casefold()
            code = self.code.casefold()

            other = other.casefold().strip()
            return name == other or code == other

        if isinstance(other, Account):
            return self.code.casefold() == other.code.casefold()

        return NotImplemented

    def get_balance(self, time: datetime = None) -> Decimal:
        if time is None:
            time = moscow_now()

        balance = self.start_balance

        for transaction in self.transactions:
            if transaction.timing >= time and transaction.timing <= self.start_date:
                balance -= transaction.value
            if transaction.timing <= time and transaction.timing >= self.start_date:
                balance += transaction.value
        return balance

    def pass_money(self,
                   target: 'Account',
                   value: Decimal,
                   currency: str = 'RUB',
                   timing: datetime = None,
                   **kwargs) -> 'Transaction':
        if timing is None:
            timing = moscow_now()

        transaction = Transaction(
            value=value,
            currency=currency,
            timing=timing,
            **kwargs,
        )
        transaction.value = -transaction.value
        twin = transaction.create_twin()

        self.transactions.append(transaction)
        target.transactions.append(twin)

        return transaction
