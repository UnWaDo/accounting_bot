from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DATETIME, DECIMAL, TIMESTAMP, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as SQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from orm.base import Base


class TransactionOrm(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(SQL_UUID(as_uuid=True), default=uuid4)

    value: Mapped[Decimal] = mapped_column(DECIMAL(scale=2))
    currency: Mapped[str] = mapped_column(String(3), default='RUB')
    timing: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                             server_default=func.now())

    reason: Mapped[Optional[str]] = mapped_column(String(20))
    category: Mapped[Optional[str]] = mapped_column(String(10))

    account_id: Mapped[int] = mapped_column(ForeignKey('accounts.id'))
    account: Mapped['AccountOrm'] = relationship(back_populates='transactions')


class AccountOrm(Base):
    __tablename__ = 'accounts'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50), unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)

    start_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=func.now())
    start_balance: Mapped[Decimal] = mapped_column(DECIMAL(scale=2),
                                                   default=Decimal())

    transactions: Mapped[List['TransactionOrm']] = relationship(
        back_populates='account', cascade='all,delete')

    type: Mapped[str]

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'account'
    }
