import random

from tests.constants import *
from tests.utils import *

from midiUtils import dataAug

SOURCE_DIR = f'{TEST_DATA_DIR}/augSource'
OUTPUT_DIR = f'{TEST_DATA_DIR}/augOutput'
EXAMPLES_DIR = f'{TEST_DATA_DIR}/examples'
FIXED_VOICES_TO_REPLACE = ["kick", "sna"]

def testAugScheme_InStyle():
    print("///////////////////////////////////////////////")
    print("Testing augmentationScheme with inStyle...")

    styleParams = {"preferredStyle": "songo", "outOfStyleProb": 0.0}
    suffix = '_inStyle'
    dataAug.augmentationScheme(SOURCE_DIR, OUTPUT_DIR, EXAMPLES_DIR, styleParams, suffix=suffix ,numTransformations = 2, fixedVoicesToReplace = FIXED_VOICES_TO_REPLACE, random_seed=SEED, debug=True)
    print(f"Output files written with suffix {suffix} in the directory {OUTPUT_DIR}")
    
def testAugScheme_OutOfStyle():
    print("///////////////////////////////////////////////")
    print("Testing augmentationScheme with outOfStyle...")

    styleParams = {"preferredStyle": "songo", "outOfStyleProb": 1.0}
    suffix = '_outOfStyle'
    dataAug.augmentationScheme(SOURCE_DIR, OUTPUT_DIR, EXAMPLES_DIR, styleParams, suffix=suffix, numTransformations = 2, fixedVoicesToReplace = FIXED_VOICES_TO_REPLACE, random_seed=SEED,debug=True)
    print(f"Output files written with suffix {suffix} in the directory {OUTPUT_DIR}")

def testAugScheme_WithOutOfStyleProb():
    print("///////////////////////////////////////////////")
    print("Testing augmentationScheme with outOfStyleProb...")

    styleParams = {"preferredStyle": "songo", "outOfStyleProb": 0.5}
    suffix = '_withOutOfStyleProb'
    dataAug.augmentationScheme(SOURCE_DIR, OUTPUT_DIR, EXAMPLES_DIR, styleParams, suffix=suffix, numTransformations = 2, numReplacements=2, random_seed=SEED,debug=True)
    print(f"Output files written with suffix {suffix} in the directory {OUTPUT_DIR}")

if __name__ == '__main__':
    clearDir(OUTPUT_DIR)

    testAugScheme_InStyle()
    testAugScheme_OutOfStyle()
    testAugScheme_WithOutOfStyleProb()