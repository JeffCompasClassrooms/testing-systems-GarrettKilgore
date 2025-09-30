from mydb import MyDB
import os




def describe_test_save_strings():
	def describe_load_strings_works_when_there_was_no_file():

		# setup
	
		# ensure that there is no test_data.dat

		if os.path.isfile("test_data.dat"):
			os.remove("test_data.dat")

		a_db = MyDB("test_data.dat")
		a_list = ['gummy', 'peanut m&ms', 'taffy', 'caramel reeses', 'werthers']

		# exercise
		a_db.saveStrings(a_list)

		# verify
		os.path.isfile("test_data.dat")
		b_list = a_db.loadStrings()

		assert(a_list == b_list)

		# teardown
		os.remove("test_data.dat")