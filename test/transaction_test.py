from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pytz import timezone
from account_test import account

from money.account import Account
from money.transaction import Transaction


@pytest.fixture
def other_account() -> Account:
    return Account(name='Other account', code=105)


@pytest.fixture
def transaction(account: Account, other_account: Account) -> Transaction:
    return account.pass_money(other_account, '100.00')


def test_created_transaction(account: Account, transaction: Transaction):
    assert len(account.transactions) == 1
    assert transaction in account.transactions


def test_created_twin(other_account: Account, transaction: Transaction):
    twin = transaction.create_twin()

    assert len(other_account.transactions) == 1
    assert twin in other_account.transactions


def test_balance(account: Account, other_account: Account,
                 transaction: Transaction):
    now = datetime.now(timezone('Europe/Moscow'))
    now += timedelta(minutes=1)

    assert account.get_balance(now) == Decimal('-100.00')
    assert other_account.get_balance(now) == Decimal('100.00')
