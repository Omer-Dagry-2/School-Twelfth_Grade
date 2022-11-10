import pickle


with open("database file name", "rb") as database_file:
    database = pickle.load(database_file)

print(database)
