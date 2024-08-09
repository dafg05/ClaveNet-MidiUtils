import random
import numpy as np
import mido
from collections import Counter

from tests.constants import *
from tests.utils import *

from midiUtils import dataAug
from midiUtils.constants import PERC_VOICES_MAPPING
from midiUtils.augExamples import SeedExamplesRetriever

SOURCE_DIR = TEST_DATA_DIR / "dataAug"
OUTPUT_DIR = TEST_OUT_DIR / "dataAug"

MIDI_TO_TRANSFORM = SOURCE_DIR / "rock_testbeat.mid"
EXAMPLES_DIR = TEST_DATA_DIR / "examples"
FIXED_VOICES_TO_REPLACE = ["kick", "sna"]

MIDO_MID = mido.MidiFile(MIDI_TO_TRANSFORM)
SER = SeedExamplesRetriever(EXAMPLES_DIR)
RNG = np.random.default_rng(SEED)
NUM_REPLACEMENTS = 2
TRACK_INDEX = 0

def testTransformMidiFile_inStyle():
    print("///////////////////////////////////////////////")
    print("Testing transformMidiFile inStyle...")

    preferredStyle = 'songo'
    outOfStyleProb = 0.0
    newMid, replacementInfo = dataAug.transformMidiFile(MIDO_MID, TRACK_INDEX, NUM_REPLACEMENTS, SER, RNG, preferredStyle, outOfStyleProb, debug=True)
    assert NUM_REPLACEMENTS == len(replacementInfo), f"Expected {NUM_REPLACEMENTS} replacements, got {len(replacementInfo)}."
    newMid.save(f"{OUTPUT_DIR}/rock_testbeat_transf_inStyle.mid")
    print(f"Output file written to {OUTPUT_DIR}")
    print(f"Replacement info: {replacementInfo}")

def testTransformMidiFile_outOfStyle():
    print("///////////////////////////////////////////////")
    print("Testing transformMidiFile outOfStyle...")

    preferredStyle = 'songo'
    outOfStyleProb = 1.0
    newMid, replacementInfo = dataAug.transformMidiFile(MIDO_MID, TRACK_INDEX, NUM_REPLACEMENTS, SER, RNG, preferredStyle, outOfStyleProb, debug=True)
    assert NUM_REPLACEMENTS == len(replacementInfo), f"Expected {NUM_REPLACEMENTS} replacements, got {len(replacementInfo)}."
    newMid.save(f"{OUTPUT_DIR}/rock_testbeat_transf_outOfStyle.mid")
    print(f"Output file written to {OUTPUT_DIR}")
    print(f"Replacement info: {replacementInfo}")

def testTransformMidiFile_withOutOfStyleProb():
    print("///////////////////////////////////////////////")
    print("Testing transformMidiFile with outOfStyleProb...")

    preferredStyle = 'songo'
    outOfStyleProb = 0.2
    newMid, replacementInfo = dataAug.transformMidiFile(MIDO_MID, TRACK_INDEX, NUM_REPLACEMENTS, SER, RNG, preferredStyle, outOfStyleProb, debug=True)
    assert NUM_REPLACEMENTS == len(replacementInfo), f"Expected {NUM_REPLACEMENTS} replacements, got {len(replacementInfo)}."
    newMid.save(f"{OUTPUT_DIR}/rock_testbeat_transf_withOutOfStyleProb.mid")
    print(f"Output file written to {OUTPUT_DIR}")
    print(f"Replacement info: {replacementInfo}")

def testTransformMidiFile_tooManyReplacements():
    print("///////////////////////////////////////////////")
    print("Testing transformMidiFile with many replacements...")

    numReplacements = 10
    try:
        newMid, _ = dataAug.transformMidiFile(MIDO_MID, TRACK_INDEX, numReplacements, SER, RNG, debug=True)
    except ValueError as e:
        print(f"Caught expected exception: {e}")

def testTransformMidiFile_exhaustCandidates():
    print("///////////////////////////////////////////////")
    print("Testing transformMidiFile when exhausting candidates...")

    preferredStyle = 'songo'
    outOfStyleProb = 0.2
    numReplacements = len(PERC_VOICES_MAPPING.keys())
    newMid, replacementInfo = dataAug.transformMidiFile(MIDO_MID, TRACK_INDEX, numReplacements, SER, RNG, preferredStyle, outOfStyleProb, debug=True)
    newMid.save(f"{OUTPUT_DIR}/rock_testbeat_transf_exhaustCandidates.mid")
    print("We expect the messages: 'Ran out of candidate tracks without repeating voices.' and 'Completely ran out of candidate tracks.' in the output.")
    print(f"Output file written to {OUTPUT_DIR}.")
    print(f"Replacement info: {replacementInfo}")
 
if __name__ == '__main__':
    clearOutputDir(OUTPUT_DIR)

    testTransformMidiFile_inStyle()
    testTransformMidiFile_outOfStyle()
    testTransformMidiFile_withOutOfStyleProb()
    testTransformMidiFile_tooManyReplacements()
    testTransformMidiFile_exhaustCandidates()

    synthesizeOutputDir(OUTPUT_DIR)
