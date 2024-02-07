from tests.constants import *
from tests.utils import *

from midiUtils.augExamples import SeedExamplesRetriever, AugSeedExample

import mido

EXAMPLES_DIR = TEST_DATA_DIR + "/examples"
OUTPUT_DIR = TEST_DATA_DIR + "/augExamplesOutput"
AUG_EXAMPLE_PATH = EXAMPLES_DIR + '/songo_kit.mid'
AUG_EXAMPLE_STYLE = 'songo'
STYLES = ['songo', 'mambo']
TEST_TRACK_PATH = OUTPUT_DIR + '/testTrack.mid'
SER = SeedExamplesRetriever(EXAMPLES_DIR)

def test_example():
    print("//////////////////////")
    print("Testing AugExample")
    example = AugSeedExample(midi_path=AUG_EXAMPLE_PATH, style=AUG_EXAMPLE_STYLE)
    assert example.midi_path == AUG_EXAMPLE_PATH, f"Expected {AUG_EXAMPLE_PATH}, got {example.midi_path}"
    assert example.style == AUG_EXAMPLE_STYLE, f"Expected {AUG_EXAMPLE_STYLE}, got {example.style}"
    assert example.filename == 'songo_kit.mid', f"Expected songo_kit.mid, got {example.filename}"
    assert example.voices == ['KICK', 'SNARE', 'HH'], f"Expected ['KICK', 'SNARE', 'HH'], got {example.voices}"

    assert example.hasVoice('KICK'), "Expected example to have kick voice"
    assert not example.hasVoice('TOM'), "Expected example to not have tom voice"

    kickTrack = example.getVoice('KICK')
    assert len(kickTrack) > 0, "Expected non-empty kick track"
    assert kickTrack[0].type == 'note_on', f"Expected note_on, got {kickTrack[0].type}"

    tomTrack = example.getVoice('TOM')
    assert len(tomTrack) == 0, f"Expected empty tom track, got track of length {len(tomTrack)}"

    print("AugExample test passed")

def test_retriever_getStyles():
    print("//////////////////////")
    print("Testing retriever getStyles")
    expectedSet = set(STYLES)
    actualSet = set(SER.styles)

    assert expectedSet == actualSet, f"Expected {expectedSet}, got {actualSet}"
    print("getStyles test passed")

def test_retriever_getExamplesByStyle():
    print("//////////////////////")
    print("Testing retriever getExamplesByStyle")
    style = 'mambo'
    examples = SER.getExamplesByStyle(style)
    assert len(examples) == 2, f"Expected 2 examples, got {len(examples)}"
    for e in examples:
        assert e.style == style, f"Expected style {style}, got {e.style}"
    print("getExamplesByStyle test passed")

def test_retriever_getExamplesOutOfStyle():
    print("//////////////////////")
    print("Testing retriever getExamplesOutOfStyle")
    style = 'mambo'
    examples = SER.getExamplesOutOfStyle(style)
    assert len(examples) == 1, f"Expected 1 examples, got {len(examples)}"
    e = examples[0]
    assert e.style == 'songo', f"Expected style songo, got {e.style}"
    print("getExamplesOutOfStyle test passed")

def test_retriever_getCandidateTracksInfo_InStyle():
    print("//////////////////////")
    print("Testing retriever getCandidateTracksInfo_InStyle")
    style = 'mambo'
    voice = 'KICK'
    info = SER.getCandidateTracksInfo(style, outOfStyle=False, voicesToExclude=[voice])
    assert len(info) == 4, f"Expected 4 candidate tracks, got {len(info)}"
    print("output must be inspected manually.")
    print(info)

def test_retriever_getCandidateTracksInfo_OutOfStyle():
    print("//////////////////////")
    print("Testing retriever getCandidateTracksInfo_OutOfStyle")
    style = 'mambo'
    voicesToExclude = ['KICK', 'HH', 'CRASH']
    info = SER.getCandidateTracksInfo(style, outOfStyle=True, voicesToExclude=voicesToExclude)
    assert len(info) == 1, f"Expected 4 candidate tracks, got {len(info)}"
    print("output must be inspected manually.")
    print(info)

def test_retriever_getTrack():
    print("//////////////////////")
    print("Testing retriever getTrack")
    filename = 'songo_kit.mid'
    voice = 'SNARE'
    track = SER.getTrack(filename, voice)
    assert len(track) > 0, "Expected non-empty track"
    mid = mido.MidiFile()
    mid.tracks.append(track)
    mid.save(TEST_TRACK_PATH)
    print(f"Track written to {TEST_TRACK_PATH}")


def test_retriever_getTrack_fileDoesNotExist():
    print("//////////////////////")
    print("Testing retriever getTrack fileDoesNotExist")
    filename = 'songo_kit.mid'
    voice = 'TOM'
    track = SER.getTrack(filename, voice)
    assert len(track) == 0, "Expected empty track"
    print("getTrack fileDoesNotExist test passed")

if __name__ == "__main__":
    clearOutputDir(OUTPUT_DIR)

    test_retriever_getStyles()
    test_retriever_getExamplesByStyle()
    test_retriever_getExamplesOutOfStyle()
    test_example()
    test_retriever_getCandidateTracksInfo_InStyle()
    test_retriever_getCandidateTracksInfo_OutOfStyle()
    test_retriever_getTrack()
    test_retriever_getTrack_fileDoesNotExist()