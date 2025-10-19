import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mydb import MyDB

def describe_mydb_system_tests():

    def describe_init_method():
        def it_creates_file_if_missing():
            test_file = "test_init.dat"
            if os.path.exists(test_file):
                os.remove(test_file)
            db = MyDB(test_file)
            assert os.path.exists(test_file)
            os.remove(test_file)

    def describe_loadStrings_method():
        def it_returns_saved_list():
            test_file = "test_load.dat"
            test_data = ['a', 'b', 'c']
            db = MyDB(test_file)
            db.saveStrings(test_data)
            loaded = db.loadStrings()
            assert loaded == test_data
            os.remove(test_file)

    def describe_saveStrings_method():
        def it_overwrites_file_with_new_list():
            test_file = "test_save.dat"
            db = MyDB(test_file)
            db.saveStrings(['x', 'y'])
            assert db.loadStrings() == ['x', 'y']
            os.remove(test_file)

    def describe_saveString_method():
        def it_appends_string_to_existing_list():
            test_file = "test_append.dat"
            db = MyDB(test_file)
            db.saveStrings(['first'])
            db.saveString('second')
            assert db.loadStrings() == ['first', 'second']
            os.remove(test_file)
