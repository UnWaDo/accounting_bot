from typing import Optional
from pydantic import BaseModel, Field


class Organization(BaseModel):
    id: Optional[int] = None

    name: str = Field(max_length=50)
    shortcut: str = Field(max_length=10)

    def __eq__(self, other):
        if isinstance(other, str):
            other = other.casefold().strip()

            return ((self.name.casefold() == other)
                    or (self.shortcut.casefold() == other))

        if isinstance(other, Organization):
            name = other.name.casefold()
            shortcut = other.shortcut.casefold()

            return ((self.name.casefold() == name)
                    and (self.shortcut.casefold() == shortcut))
        return NotImplemented
