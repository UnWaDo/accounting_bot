import configparser
from decimal import Decimal
from typing import List

import orm.api
import pytest
import pytest_asyncio
from money.account import Account
from money.bank_account import BankAccount
from money.organization import Organization
from orm.account import AccountOrm, TransactionOrm
from orm.api import (add_transactions, create_account, delete_account,
                     end_connection, get_account_details, get_accounts,
                     get_bank_account_details, get_bank_accounts,
                     get_organization)
from orm.bank_account import BankAccountOrm
from orm.base import Base
from orm.exc import InvalidFieldsError
from orm.organization import OrganizationOrm
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

config = configparser.ConfigParser()
config.read('settings.ini')

USER = config['test']['DbUser']
PASSWORD = config['test']['DbPassword']
HOST = config['test']['DbHost']
DB_NAME = config['test']['DbDatabase']

DB_URL = ('postgresql+asyncpg://'
          f'{USER}:{PASSWORD}@'
          f'{HOST}/{DB_NAME}')

async_engine = create_async_engine(DB_URL, pool_size=10, max_overflow=10)
async_session = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)

orm.api.engine = async_engine
orm.api.async_session = async_session


@pytest.fixture
def accounts() -> List[AccountOrm]:
    accounts = [Account(name=f'Account {i}', code=i) for i in range(1, 5)]
    accounts[0].pass_money(accounts[1], '100.00')
    accounts[0].pass_money(accounts[2], '-200.00')

    orm_accounts = []
    for account in accounts:
        transactions = [
            TransactionOrm(**t.model_dump()) for t in account.transactions
        ]
        data = account.model_dump()
        data['transactions'] = transactions
        orm_accounts.append(AccountOrm(**data))
    return orm_accounts


@pytest.fixture
def organizations() -> List[OrganizationOrm]:
    return [
        OrganizationOrm(name=f'Organization {i}', shortcut=f'org {i}')
        for i in range(1, 5)
    ]


@pytest.fixture
def bank_accounts(organizations: List[OrganizationOrm]) -> List[AccountOrm]:
    accounts = [
        BankAccount(name=f'Bank account {i}',
                    code=i * 100,
                    bank=Organization.model_validate(organizations[(i - 1) //
                                                                   2 * 2],
                                                     from_attributes=True))
        for i in range(1, 5)
    ]
    accounts[0].pass_money(accounts[1], '100.00')
    accounts[0].pass_money(accounts[2], '-200.00')

    orm_accounts = []
    for i, account in enumerate(accounts, start=1):
        transactions = [
            TransactionOrm(**t.model_dump()) for t in account.transactions
        ]
        data = account.model_dump()
        data['transactions'] = transactions
        data['bank'] = organizations[(i - 1) // 2 * 2]
        orm_accounts.append(BankAccountOrm(**data))
    return orm_accounts


@pytest_asyncio.fixture(autouse=True)
async def prepare_database(organizations, accounts, bank_accounts):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async with session.begin():
            session.add_all(organizations)
            session.add_all(accounts)
            session.add_all(bank_accounts)


@pytest_asyncio.fixture(autouse=True)
async def close_database():
    yield

    await end_connection()


@pytest.mark.asyncio
async def test_get_accounts(accounts, bank_accounts):
    db_accounts = await get_accounts()

    assert len(accounts + bank_accounts) == len(db_accounts)

    account_names = [a.name for a in accounts + bank_accounts]
    for account in db_accounts:
        assert account.name in account_names


@pytest.mark.asyncio
async def test_get_bank_accounts(bank_accounts):
    db_accounts = await get_bank_accounts()

    assert len(bank_accounts) == len(db_accounts)

    account_names = [a.name for a in bank_accounts]
    for account in db_accounts:
        assert account.name in account_names


@pytest.mark.asyncio
async def test_get_bank_accounts(bank_accounts):
    db_accounts = await get_bank_accounts()

    assert len(bank_accounts) == len(db_accounts)

    account_names = [a.name for a in bank_accounts]
    for account in db_accounts:
        assert account.name in account_names


@pytest.mark.asyncio
async def test_get_account_details(accounts):
    account = accounts[0]
    db_account = await get_account_details(account.id)

    assert account.name == db_account.name
    assert account.code == db_account.code
    assert account.start_date == db_account.start_date
    assert account.start_balance == db_account.start_balance
    assert len(account.transactions) == len(db_account.transactions)


@pytest.mark.asyncio
async def test_get_bank_account_details(bank_accounts):
    account = bank_accounts[0]
    db_account = await get_bank_account_details(account.id)

    assert account.name == db_account.name
    assert account.code == db_account.code
    assert account.start_date == db_account.start_date
    assert account.start_balance == db_account.start_balance
    assert len(account.transactions) == len(db_account.transactions)

    assert account.bank.name == db_account.bank.name
    assert account.bank.shortcut == db_account.bank.shortcut


@pytest.mark.asyncio
async def test_delete_account_by_id(accounts):
    id = accounts[2].id
    await delete_account(id=id)

    details = await get_account_details(id)
    assert details is None


@pytest.mark.asyncio
async def test_delete_account_by_object(accounts):
    account = await get_account_details(accounts[0].id)
    account.name = account.name.upper()

    await delete_account(account=account)

    details = await get_account_details(accounts[0].id)
    assert details is None


@pytest.mark.asyncio
async def test_new_account():
    account = Account(name='One more', code=9999)

    account_orm = await create_account(account)

    details = await get_account_details(account_orm.id)
    assert details is not None


@pytest.mark.asyncio
async def test_add_existing_name(accounts):
    existing = accounts[0]
    account = Account(name=existing.name, code=9999)

    with pytest.raises(InvalidFieldsError) as e:
        account_orm = await create_account(account)

    assert e.value.fields == [('name', existing.name)]


@pytest.mark.asyncio
async def test_add_existing_code(accounts):
    existing = accounts[0]
    account = Account(name='Non existing name', code=existing.code)

    with pytest.raises(InvalidFieldsError) as e:
        account_orm = await create_account(account)

    assert e.value.fields == [('code', str(existing.code))]


@pytest.mark.asyncio
async def test_add_account_with_long_code(accounts):
    with pytest.raises(ValidationError):
        account = Account(name='One more', code='123409875665' * 2)


@pytest.mark.asyncio
async def test_add_account_with_long_name():
    with pytest.raises(ValidationError):
        account = Account(name='One more' * 100, code=9999)


@pytest.mark.asyncio
async def test_add_bank_account(organizations):
    account = BankAccount(name='One more',
                          code=9999,
                          bank=Organization.model_validate(
                              organizations[0], from_attributes=True))

    account_orm = await create_account(account)

    details = await get_bank_account_details(account_orm.id)
    assert details is not None

    bank = await get_organization(organizations[0].id)
    assert bank is not None
    assert details.bank.name == bank.name
    assert details.bank.shortcut == bank.shortcut


@pytest.mark.asyncio
async def test_add_bank_account_new_bank(organizations):
    account = BankAccount(name='One more',
                          code=9999,
                          bank=Organization(name='One more', shortcut='more'))

    account_orm = await create_account(account)

    details = await get_bank_account_details(account_orm.id)
    assert details is not None

    bank = await get_organization(len(organizations) + 1)
    assert bank is not None
    assert details.bank.name == bank.name
    assert details.bank.shortcut == bank.shortcut


@pytest.mark.asyncio
async def test_pass_money(accounts: List[AccountOrm]):
    source = await get_account_details(accounts[0].id)
    target = await get_account_details(accounts[-1].id)

    expected_balance = (
        source.get_balance() - Decimal('100'),
        target.get_balance() + Decimal('100'),
    )
    expected_count = (
        len(source.transactions) + 1,
        len(target.transactions) + 1,
    )

    source.pass_money(
        target,
        '100.00',
    )

    await add_transactions(source)
    await add_transactions(target)

    source = await get_account_details(accounts[0].id)
    target = await get_account_details(accounts[-1].id)

    assert (
        len(source.transactions),
        len(target.transactions),
    ) == expected_count
    assert (source.get_balance(), target.get_balance()) == expected_balance


@pytest.mark.asyncio
async def test_pass_money_starting_empty(accounts: List[AccountOrm]):
    source = await get_account_details(accounts[0].id)
    target = await get_account_details(accounts[-1].id)

    expected_balance = (
        source.get_balance() - Decimal('100'),
        target.get_balance() + Decimal('100'),
    )
    expected_count = (
        len(source.transactions) + 1,
        len(target.transactions) + 1,
    )

    source = await get_account_details(accounts[0].id, with_transactions=False)
    target = await get_account_details(accounts[-1].id,
                                       with_transactions=False)
    source.pass_money(
        target,
        '100.00',
    )

    await add_transactions(source)
    await add_transactions(target)

    source = await get_account_details(accounts[0].id)
    target = await get_account_details(accounts[-1].id)

    assert (
        len(source.transactions),
        len(target.transactions),
    ) == expected_count
    assert (source.get_balance(), target.get_balance()) == expected_balance
