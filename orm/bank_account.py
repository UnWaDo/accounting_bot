from datetime import timedelta
from decimal import Decimal

from sqlalchemy import DECIMAL, ForeignKey, Interval
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.account import AccountOrm
from orm.organization import OrganizationOrm


class BankAccountOrm(AccountOrm):
    __tablename__ = 'bank_accounts'
    id: Mapped[int] = mapped_column(ForeignKey('accounts.id'),
                                    primary_key=True)
    annual_interest: Mapped[Decimal] = mapped_column(DECIMAL(scale=2),
                                                     default=Decimal())
    interest_period: Mapped[timedelta] = mapped_column(Interval(),
                                                       default=timedelta(0))

    bank_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    bank: Mapped[OrganizationOrm] = relationship()

    __mapper_args__ = {'polymorphic_identity': 'bank_account'}
