from tests.constants import *

from midiUtils.augExamples import AugExamplesRetriever, AugExample

EXAMPLES_DIR = TEST_DATA_DIR + "/examples"
AUG_EXAMPLE_PATH = EXAMPLES_DIR + '/songo_kit.mid'
AUG_EXAMPLE_STYLE = 'songo'
STYLES = ['songo', 'mambo']
AER = AugExamplesRetriever(EXAMPLES_DIR)

def test_example():
    print("//////////////////////")
    print("Testing AugExample")
    example = AugExample(midi_path=AUG_EXAMPLE_PATH, style=AUG_EXAMPLE_STYLE)
    assert example.midi_path == AUG_EXAMPLE_PATH, f"Expected {AUG_EXAMPLE_PATH}, got {example.midi_path}"
    assert example.style == AUG_EXAMPLE_STYLE, f"Expected {AUG_EXAMPLE_STYLE}, got {example.style}"

    assert example.hasVoice('kick'), "Expected example to have kick voice"
    assert not example.hasVoice('tom'), "Expected example to not have tom voice"

    kickTrack = example.getVoice('kick')
    assert len(kickTrack) > 0, "Expected non-empty kick track"
    assert kickTrack[0].type == 'note_on', f"Expected note_on, got {kickTrack[0].type}"

    tomTrack = example.getVoice('tom')
    assert len(tomTrack) == 0, f"Expected empty tom track, got track of length {len(tomTrack)}"

    print("AugExample test passed")

def test_retriever_getStyles():
    print("//////////////////////")
    print("Testing retriever getStyles")
    expectedSet = set(STYLES)
    actualSet = set(AER.styles)

    assert expectedSet == actualSet, f"Expected {expectedSet}, got {actualSet}"
    print("getStyles test passed")

def test_retriever_getExamplesByStyle():
    print("//////////////////////")
    print("Testing retriever getExamplesByStyle")
    style = 'mambo'
    examples = AER.getExamplesByStyle(style)
    assert len(examples) == 2, f"Expected 2 examples, got {len(examples)}"
    for e in examples:
        assert e.style == style, f"Expected style {style}, got {e.style}"
    print("getExamplesByStyle test passed")

def test_retriever_getExamplesOutOfStyle():
    print("//////////////////////")
    print("Testing retriever getExamplesOutOfStyle")
    style = 'mambo'
    examples = AER.getExamplesOutOfStyle(style)
    assert len(examples) == 1, f"Expected 1 examples, got {len(examples)}"
    e = examples[0]
    assert e.style == 'songo', f"Expected style songo, got {e.style}"


if __name__ == "__main__":
    test_retriever_getStyles()
    test_retriever_getExamplesByStyle()
    test_retriever_getExamplesOutOfStyle()
    test_example()