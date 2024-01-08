import os
import utils

from constants import *

def splitMidi(sourceDir, splitDir=SPLIT_DIR):    
    if len(os.listdir(splitDir)) > 0:
        raise Exception(f"Split directory {splitDir} is not empty. Please clear it before splitting.")
    
    splitErrors = 0
    totalMidi = 0

    for f in os.listdir(sourceDir):
        if f.endswith(".mid"):
            try:
                utils.splitMidiFileByBarSteps(f"{sourceDir}/{f}", splitDir, 2)
                totalMidi += 1
            except Exception as e:
                print(f"Error splitting {f}: {e}")
                splitErrors += 1
    print(f"Split {totalMidi} files, {splitErrors} errors occurred. ")