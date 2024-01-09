import configparser
from typing import Optional, Sequence, Union

from money.account import Account
from money.bank_account import BankAccount
from money.organization import Organization
from money.stock_account import StockAccount
from orm.account import AccountOrm, TransactionOrm
from orm.bank_account import BankAccountOrm
from orm.exc import InvalidFieldsError
from orm.organization import OrganizationOrm
from orm.stock_account import StockAccountOrm
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import joinedload, noload

config = configparser.ConfigParser()
config.read('settings.ini')

USER = config['orm']['User']
PASSWORD = config['orm']['Password']
HOST = config['orm']['Host']
DB_NAME = config['orm']['Database']

DB_URL = ('postgresql+asyncpg://'
          f'{USER}:{PASSWORD}@'
          f'{HOST}/{DB_NAME}')

engine = create_async_engine(DB_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def end_connection() -> None:
    await engine.dispose()


async def _get_accounts(
    type: Union[AccountOrm, BankAccountOrm, StockAccountOrm]
) -> Sequence[Union[AccountOrm, BankAccountOrm, StockAccountOrm]]:
    async with async_session() as session:
        async with session.begin():
            statement = select(type).order_by(type.name)

            result = await session.execute(statement)
            return result.scalars().all()


async def get_accounts() -> Sequence[AccountOrm]:
    return await _get_accounts(AccountOrm)


async def get_bank_accounts() -> Sequence[BankAccountOrm]:
    return await _get_accounts(BankAccountOrm)


async def get_stock_accounts() -> Sequence[StockAccountOrm]:
    return await _get_accounts(StockAccountOrm)


async def get_organizations() -> Sequence[OrganizationOrm]:
    async with async_session() as session:
        async with session.begin():
            statement = select(OrganizationOrm).order_by(OrganizationOrm.name)

            result = await session.execute(statement)
            return result.scalars().all()


async def get_organization(id: int) -> Organization:
    async with async_session() as session:
        async with session.begin():
            statement = select(OrganizationOrm).where(OrganizationOrm.id == id)

            result = await session.execute(statement)
            orm = result.scalar()
    return Organization.model_validate(orm, from_attributes=True)


async def _get_account_details(
    id: int,
    type: Union[AccountOrm, BankAccountOrm, StockAccountOrm],
    with_transactions=True,
) -> Union[AccountOrm, BankAccountOrm, StockAccountOrm]:
    async with async_session() as session:
        async with session.begin():
            statement = select(type).where(type.id == id)

            if with_transactions:
                statement = statement.options(joinedload(type.transactions))
            else:
                statement = statement.options(noload(type.transactions))

            if type == BankAccountOrm:
                statement = statement.options(joinedload(BankAccountOrm.bank))
            if type == StockAccountOrm:
                statement = statement.options(
                    joinedload(StockAccountOrm.broker))

            result = await session.execute(statement)
            return result.scalar()


async def get_account_details(
    id: int,
    with_transactions=True,
) -> Optional[Account]:
    account = await _get_account_details(
        id,
        AccountOrm,
        with_transactions=with_transactions,
    )
    if account is None:
        return None
    return Account.model_validate(account, from_attributes=True)


async def get_bank_account_details(
    id: int,
    with_transactions=True,
) -> Optional[BankAccount]:
    account = await _get_account_details(
        id,
        BankAccountOrm,
        with_transactions=with_transactions,
    )
    if account is None:
        return None
    return BankAccount.model_validate(account, from_attributes=True)


async def get_stock_account_details(
    id: int,
    with_transactions=True,
) -> Optional[StockAccount]:
    account = await _get_account_details(
        id,
        StockAccountOrm,
        with_transactions=with_transactions,
    )
    if account is None:
        return None
    return StockAccount.model_validate(account, from_attributes=True)


async def _get_organization(organization: Organization,
                            session: AsyncSession) -> OrganizationOrm:
    if organization.id is not None:
        organization_orm = await session.get(OrganizationOrm, organization.id)
    else:
        statement = (select(OrganizationOrm).where(
            OrganizationOrm.name == organization.name))

        result = await session.execute(statement)
        organization_orm = result.scalar()

    if organization_orm is None:
        organization_orm = OrganizationOrm(**organization.model_dump())

    return organization_orm


async def create_account(account: Account) -> AccountOrm:
    transactions = []
    for transaction in account.transactions:
        transactions.append(TransactionOrm(**transaction.model_dump()))

    data = account.model_dump()
    data['transactions'] = transactions

    async with async_session() as session:
        async with session.begin():
            if isinstance(account, BankAccount):
                data['bank'] = await _get_organization(account.bank, session)
                new_account = BankAccountOrm(**data)
            elif isinstance(account, StockAccount):
                data['broker'] = await _get_organization(
                    account.broker, session)
                new_account = StockAccountOrm(**data)
            else:
                new_account = AccountOrm(**data)

            session.add(new_account)

            try:
                await session.commit()
            except DBAPIError as e:
                raise InvalidFieldsError(e)

    return new_account


async def delete_account(*, account: Account = None, id: int = None):
    if account is None and id is None:
        raise ValueError('One of the arguments must be not None')

    id = id or account.id

    async with async_session() as session:
        async with session.begin():
            if id is not None:
                account_orm = await session.get(AccountOrm, id)
            else:
                statement = select(AccountOrm).where(
                    func.lower(AccountOrm.name) == account.name.casefold())

                result = await session.execute(statement)
                account_orm = result.scalar()

            await session.delete(account_orm)
            await session.commit()


async def add_transactions(account: Account):
    async with async_session() as session:
        async with session.begin():
            transactions = [
                TransactionOrm(**t.model_dump()) for t in account.transactions
            ]
            if account.id is not None:
                account_orm = await session.get(
                    AccountOrm,
                    account.id,
                    options=[joinedload(AccountOrm.transactions)])
            else:
                statement = select(AccountOrm).where(
                    func.lower(AccountOrm.name)
                    == account.name.casefold()).options(
                        joinedload(TransactionOrm))

                result = await session.execute(statement)
                account_orm = result.scalar()

            uuids = [t.uuid for t in account_orm.transactions]
            for transaction in transactions:
                if transaction.uuid in uuids:
                    continue
                transaction.account = account_orm
                session.add(transaction)

            try:
                await session.commit()
            except DBAPIError as e:
                raise InvalidFieldsError(e)
