from main import config
from main.models import Base
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

db_engine = create_engine(config.DATABASE_URL)
session_maker = sessionmaker(bind=db_engine)


def db_session():
    return session_maker()


class Session:

    def __enter__(self):
        self.s = db_session()

        return self.s

    def __exit__(self, *args):
        self.s.close()


def construct_db(recreate=False):
    try:
        # check to see if database exists
        db_engine.connect()
        db_engine.execute('SELECT 1;')
        if not recreate:
            return
        Base.metadata.drop_all(db_engine)  # recreate db if specified
    except OperationalError:
        # database does not exist
        pass

    Base.metadata.create_all(db_engine)
