import pickle

savefile = "list.pkl"
list_null = []

with open(savefile, "wb") as f:
    pickle.dump(list_null, f, -1)
