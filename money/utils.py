from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ValidationError
from pytz import timezone


def moscow_now() -> datetime:
    return datetime.now(timezone('Europe/Moscow'))


def validate_field(model: BaseModel, field: str, value: Any) -> Optional[str]:
    try:
        model.__pydantic_validator__.validate_assignment(
            model.model_construct(),
            field,
            value,
        )
    except ValidationError as e:
        error = e.errors()[0]
        return error['msg']
