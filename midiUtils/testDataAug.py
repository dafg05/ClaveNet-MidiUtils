import random

from midiUtils import dataAug
from midiUtils.constants import *

SOURCE_DIR = DATA_AUG_SOURCE_DIR + "/test"
OUTPUT_DIR = DATA_AUG_OUTPUT_DIR + "/test"
EXAMPLES_TEST_DIR = EXAMPLES_DIR + "/test"
FIXED_PARTS_TO_REPLACE = ["kick", "sna"]

def test1():
    styleParams = {"preferredStyle": "songo", "outOfStyleProb": 0.0}
    dataAug.augmentationScheme(SOURCE_DIR, OUTPUT_DIR, EXAMPLES_TEST_DIR, styleParams, numTransformations = 2, fixedPartsToReplace = FIXED_PARTS_TO_REPLACE)
    print("test1 done")
    
def test2():
    styleParams = {"preferredStyle": "songo", "outOfStyleProb": 1.0}
    dataAug.augmentationScheme(SOURCE_DIR, OUTPUT_DIR, EXAMPLES_TEST_DIR, styleParams, numTransformations = 2, fixedPartsToReplace = FIXED_PARTS_TO_REPLACE)

def test3():
    styleParams = {"preferredStyle": "songo", "outOfStyleProb": 0.5}
    dataAug.augmentationScheme(SOURCE_DIR, OUTPUT_DIR, EXAMPLES_TEST_DIR, styleParams, numTransformations = 2, numReplacements=2)

if __name__ == '__main__':
    random.seed(2)

    test1()
    # test2()
    # test3()
