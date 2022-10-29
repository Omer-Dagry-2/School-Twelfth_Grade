import pickle


with open("database", "rb") as database_file:
    database = pickle.load(database_file)

print(database)
