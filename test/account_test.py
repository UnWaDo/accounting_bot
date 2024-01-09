from pydantic import TypeAdapter
import pytest
from money.account import Account
from money.utils import validate_field


@pytest.fixture
def account() -> Account:
    return Account(name='Some account', code=100)


@pytest.mark.parametrize('value', [
    'Some account',
    'SOME account',
    'some account ',
    '    some account ',
])
def test_account_equal_string(account: Account, value: str):
    assert account == value


def test_account_equal_int(account: Account):
    assert account == account.code


@pytest.mark.parametrize('value', [
    'Some arcount',
    'arcount some',
    'Ark',
    '',
    'lol',
])
def test_account_unequal_string(account: Account, value: str):
    assert account != value


def test_account_unequal_int(account: Account):
    assert account != (int(account.code) + 100) * 2


@pytest.mark.parametrize('name,code', [('Lol account', 100),
                                       ('Some account', 100),
                                       ('SOME ACCOUNT', 100)])
def test_account_equal_obj(account: Account, name: str, code: int):
    other = Account(name=name, code=code)
    assert account == other


@pytest.mark.parametrize('name,code', [('Lol account', 102),
                                       ('Some account', 101),
                                       ('Lol account', 101)])
def test_account_unequal_obj(account: Account, name: str, code: int):
    other = Account(name=name, code=code)
    assert account != other


def test_partial_initialization_valid():
    message = validate_field(Account, 'code', '123123123123')
    assert message is None


def test_partial_initialization_invalid():
    message = validate_field(Account, 'code', '123409875665' * 2)
    assert message == 'String should have at most 20 characters'
