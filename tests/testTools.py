from tests.constants import *
from tests.utils import *

from midiUtils.tools import *

import mido

SOURCE_DIR = TEST_DATA_DIR / "tools"
OUTPUT_DIR = TEST_OUT_DIR / "tools"

MERGEE_1 = SOURCE_DIR / 'mergee1.mid'
MERGEE_2 = SOURCE_DIR / 'mergee2.mid'
MERGEE_3 = SOURCE_DIR / 'mergee3.mid'
TO_TRIM = SOURCE_DIR / 'toTrim.mid'

def test_isTrackEmpty():
    print("///////////////////////////////////////////////")
    print("Testing isTrackEmpty...")

    mid = mido.MidiFile(TO_TRIM)
    nonEmptyTrack = mid.tracks[0]
    assert not isTrackEmpty(nonEmptyTrack), "nonEmptyTrack shows as empty"

    emptyTrack = mido.MidiTrack()
    emptyTrack.append(mido.MetaMessage('end_of_track'))
    assert isTrackEmpty(emptyTrack), "emptyTrack shows as non-empty"
    print("isTrackEmpty passed")

def test_mergeMultipleTracks():
    print("///////////////////////////////////////////////")
    print("Testing mergeMultipleTracks...")
    mid1 = mido.MidiFile(MERGEE_1)
    mid2 = mido.MidiFile(MERGEE_2)
    mid3 = mido.MidiFile(MERGEE_3)
    track1 = mid1.tracks[0]
    track2 = mid2.tracks[0]
    track3 = mid3.tracks[0]
    noteTracks = [track2, track3]

    mergedTrack = mergeMultipleTracks(trackWithMetaData=track1, noteTracks=noteTracks)
    
    mid1.tracks[0] = mergedTrack
    mid1.save(OUTPUT_DIR / 'merged.mid')
    print(f"Saved to {OUTPUT_DIR}/merged.mid")

def test_trimMidiTrack():
    print("///////////////////////////////////////////////")
    print("Testing trimMidiTrack...")
    
    mid = mido.MidiFile(TO_TRIM)
    track = mid.tracks[0]

    trimmedTrack = trimMidiTrack(track=track, startBar=1, endBar=2, beatsPerBar=4, ticksPerBeat=mid.ticks_per_beat)

    mid.tracks[0] = trimmedTrack
    mid.save(OUTPUT_DIR / 'trimmed.mid')
    print(f"Saved to {OUTPUT_DIR}/trimmed.mid")

def test_allMessagesToChannel():
    print("///////////////////////////////////////////////")
    print("Testing allMessagesToChannel...")

    mid = mido.MidiFile(TO_TRIM)
    track = mid.tracks[0]

    newTrack = allMessagesToChannel(track, 3)
    
    for msg in newTrack:
        if isinstance(msg, mido.Message):
            assert msg.channel == 3, f"msg.channel is {msg.channel}, expected 3"
    print("allMessagesToChannel passed")

if __name__ == "__main__":
    clearOutputDir(OUTPUT_DIR)

    test_isTrackEmpty()
    test_mergeMultipleTracks()
    test_trimMidiTrack()
    test_allMessagesToChannel()

