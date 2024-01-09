import configparser

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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
