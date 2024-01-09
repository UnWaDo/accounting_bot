from datetime import timedelta
from decimal import Decimal

from sqlalchemy import DECIMAL, ForeignKey, Interval
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.account import AccountOrm
from orm.organization import OrganizationOrm


class StockAccountOrm(AccountOrm):
    __tablename__ = 'stock_accounts'
    id: Mapped[int] = mapped_column(ForeignKey('accounts.id'),
                                    primary_key=True)
    is_iia: Mapped[bool] = mapped_column(default=False)
    stock_value: Mapped[Decimal] = mapped_column(DECIMAL(scale=2),
                                                 default=Decimal())

    broker_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    broker: Mapped[OrganizationOrm] = relationship()

    __mapper_args__ = {'polymorphic_identity': 'stock_account'}
