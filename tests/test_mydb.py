import os.path
import pickle
import pytest
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mydb import MyDB

todo = pytest.mark.skip(reason='todo: pending spec')

@pytest.fixture
def db_filename():
    return "mydatabase.db"

@pytest.fixture
def nonempty_db(db_filename):
    with open(db_filename, 'wb') as f:
        pickle.dump(['stuff', 'more stuff'], f)

@pytest.fixture(autouse=True)
def cleanup(db_filename):
    yield
    if os.path.exists(db_filename):
        os.remove(db_filename)

def describe_MyDB():

    def describe_init():

        def it_assigns_fname_attribute(db_filename):
            db = MyDB(db_filename)
            assert db.fname == db_filename

        def it_creates_empty_database_if_it_does_not_exist(db_filename):
            assert not os.path.isfile(db_filename)
            db = MyDB(db_filename)
            assert os.path.isfile(db_filename)
            with open(db_filename, 'rb') as f:
                assert pickle.load(f) == []

    def describe_loadStrings():

        def it_loads_empty_database_if_no_data(db_filename):
            db = MyDB(db_filename)
            assert db.loadStrings() == []

        def it_loads_existing_data(nonempty_db, db_filename):
            db = MyDB(db_filename)
            assert db.loadStrings() == ['stuff', 'more stuff']

    def describe_saveStrings():

        def it_overwrites_existing_data(db_filename):
            db = MyDB(db_filename)
            db.saveStrings(['a', 'b', 'c'])
            with open(db_filename, 'rb') as f:
                assert pickle.load(f) == ['a', 'b', 'c']

        def it_saves_empty_list(db_filename):
            db = MyDB(db_filename)
            db.saveStrings([])
            with open(db_filename, 'rb') as f:
                assert pickle.load(f) == []

    def describe_saveString():

        def it_appends_to_empty_database(db_filename):
            db = MyDB(db_filename)
            db.saveString('new')
            assert db.loadStrings() == ['new']

        def it_appends_to_existing_data(nonempty_db, db_filename):
            db = MyDB(db_filename)
            db.saveString('extra')
            assert db.loadStrings() == ['stuff', 'more stuff', 'extra']
