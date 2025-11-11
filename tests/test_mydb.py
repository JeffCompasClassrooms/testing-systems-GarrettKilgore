import os.path
import pickle
import pytest
import sys
import stat
import builtins
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

    def describe_non_string_input():

        def it_accepts_non_string_input(db_filename):
            db = MyDB(db_filename)
            db.saveString(123)
            assert db.loadStrings() == [123]

    def describe_invalid_pickle_format():

        def it_raises_on_invalid_pickle_format(db_filename):
            with open(db_filename, 'wb') as f:
                f.write(b"not a pickle")
            db = MyDB(db_filename)
            with pytest.raises(Exception):
                db.loadStrings()

    def describe_multiple_appends():

        def it_accumulates_multiple_appends(db_filename):
            db = MyDB(db_filename)
            db.saveString("one")
            db.saveString("two")
            db.saveString("three")
            assert db.loadStrings() == ["one", "two", "three"]

    def describe_empty_string():

        def it_stores_empty_string(db_filename):
            db = MyDB(db_filename)
            db.saveString("")
            assert db.loadStrings() == [""]

    def describe_saveStrings_mixed_types():
   
        def it_saves_mixed_type_list(db_filename):
            db = MyDB(db_filename)
            mixed = ["text", 42, {"key": "value"}, [1, 2]]
            db.saveStrings(mixed)
            assert db.loadStrings() == mixed

    def describe_file_permissions():

        def it_raises_on_write_to_read_only_file(db_filename, monkeypatch):
            db = MyDB(db_filename)

            def fake_open(*args, **kwargs):
                raise PermissionError("File is read-only")

            monkeypatch.setattr(builtins, "open", fake_open)
            with pytest.raises(PermissionError):
                db.saveStrings(["fail"])

    def describe_large_input():

        def it_handles_very_large_string(db_filename):
            db = MyDB(db_filename)
            long_string = "x" * 100_000
            db.saveString(long_string)
            assert db.loadStrings() == [long_string]


    def describe_concurrent_access():

        def it_preserves_data_across_instances(db_filename):
            db1 = MyDB(db_filename)
            db2 = MyDB(db_filename)
            db1.saveString("first")
            db2.saveString("second")
            assert db1.loadStrings() == ["first", "second"]