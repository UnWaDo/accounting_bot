from typing import Callable, Optional, Sequence

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from pydantic import BaseModel

from money.utils import validate_field

TIME_FORMAT = '%X'
DATE_FORMAT = '%a, %x'
DATETIME_FORMAT = '%x %X'


async def unrecognized_handler(message: Message):
    await message.answer('I do not understand...')


async def unrecognized_callback(query: CallbackQuery):
    await query.answer('This action is outdated.'
                       ' Send /cancel command to return to main menu')


def is_in_list(text: str, options: Sequence[str]) -> Optional[str]:
    if text in options:
        return None
    return 'Option is not allowed'


async def collect_object_field(
    message: Message,
    state: FSMContext,
    model: BaseModel,
    field: str,
    dict_name: str = None,
    parser: Callable[[str], str] = None,
) -> Optional[str]:
    return await collect_value(
        message,
        state,
        field=field,
        validator=lambda x: validate_field(model, field, x),
        dict_name=dict_name,
        parser=parser,
    )


async def collect_value(
    message: Message,
    state: FSMContext,
    validator: Callable[[str], Optional[str]],
    field: str = None,
    dict_name: str = None,
    parser: Callable[[str], str] = None,
) -> Optional[str]:
    if parser is not None:
        text = parser(message.text)
    else:
        text = message.text

    error = validator(text)
    if error is not None:
        await message.answer(f'Invalid value: {error}. Try again')
        return None

    if field is None:
        return text

    if dict_name is None:
        await state.update_data({field: text})
    else:
        data = await state.get_data()
        dict_data = data.get(dict_name, {})
        dict_data[field] = text

        await state.update_data({dict_name: dict_data})
    return text
