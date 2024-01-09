import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field

from money.utils import moscow_now

TRANSACTION_RE = re.compile(
    r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}) #'
    r' (\w{32}) - ([+-]\d+\.\d+) (\w+)'
    r' - ([\w\s]+)? - ([\w\s]+)?')


class Transaction(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)
    value: Decimal = Field(decimal_places=2)
    currency: str = 'RUB'
    timing: AwareDatetime = Field(default_factory=moscow_now)
    reason: Optional[str] = None
    category: Optional[str] = None

    def create_twin(self) -> 'Transaction':
        return Transaction(
            uuid=self.uuid,
            value=-self.value,
            currency=self.currency,
            timing=self.timing,
            reason=self.reason,
            category=self.category,
        )

    def __str__(self) -> str:
        reason = self.reason or ''
        category = self.category or ''

        return (f'{self.timing.isoformat()} # {self.uuid.hex} - '
                f'{self.value:+.2f} {self.currency} '
                f'- {reason} - {category}')

    @staticmethod
    def from_str(string: str) -> 'Transaction':
        match = TRANSACTION_RE.match(string)
        if match is None:
            raise ValueError('String is not a valid Transaction string')

        data = {}
        data['timing'] = match.group(1)
        data['uuid'] = match.group(2)
        data['value'] = match.group(3)
        data['currency'] = match.group(4)
        data['reason'] = match.group(5) or None
        data['category'] = match.group(6) or None

        return Transaction.model_validate(data)

    def __eq__(self, other) -> bool:
        if isinstance(other, UUID):
            return self.uuid == other
        if isinstance(other, Transaction):
            return self.uuid == other.uuid and self.value == other.value
        if not isinstance(other, Transaction):
            return NotImplemented

    def is_twin(self, other: 'Transaction') -> bool:
        return self.uuid == other.uuid and self.value == -other.value
