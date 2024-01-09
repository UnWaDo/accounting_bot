import asyncio
import configparser
import locale

from aiogram import Bot
from aiogram.enums import ParseMode

from bot.logistics import dispatcher

config = configparser.ConfigParser()
config.read('settings.ini')

API_TOKEN = config['bot']['ApiKey']


async def main() -> None:
    bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)

    return await dispatcher.start_polling(bot)


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    asyncio.run(main())
