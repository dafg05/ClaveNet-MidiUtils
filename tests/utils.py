import os

def clearDir(dir):
    for f in os.listdir(dir):
        os.remove(f"{dir}/{f}")