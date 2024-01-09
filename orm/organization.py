from orm.base import Base

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class OrganizationOrm(Base):
    __tablename__ = 'organizations'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50), unique=True)
    shortcut: Mapped[str] = mapped_column(String(10), unique=True)
