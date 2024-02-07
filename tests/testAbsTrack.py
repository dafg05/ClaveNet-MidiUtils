from tests.constants import *
from tests.utils import *

from midiUtils.constants import NOTE_OFF, NOTE_ON, END_OF_TRACK
from midiUtils.absTrack import AbsoluteTimeTrack, AbsoluteTimeMidiMessage

import mido
import random

SOURCE_DIR = f'{TEST_DATA_DIR}/absTrackSource'
OUTPUT_DIR = f'{TEST_DATA_DIR}/absTrackOutput'

MIDI_FILE = SOURCE_DIR + "/1_rock_110_beat_4-4_slice_208.mid"
EXCLUDE_OUT = OUTPUT_DIR + "/exclude_pitches.mid"
INCLUDE_OUT = OUTPUT_DIR + "/include_pitches.mid"
MERGEE_1 = SOURCE_DIR + "/mergee1.mid"
MERGEE_2 = SOURCE_DIR + "/mergee2.mid"
MERGEE_3 = SOURCE_DIR + "/mergee3.mid"
SIMPLE_MERGED_OUT = OUTPUT_DIR + "/merged_simple.mid"
MULTIPLE_MERGED_OUT = OUTPUT_DIR + "/merged_multiple.mid"
OFFSET_TIME_OUT = OUTPUT_DIR + "/offset_time.mid"
OFFSET_VELOCITY_OUT = OUTPUT_DIR + "/offset_velocity.mid"

TEST_PITCHES = [36,44] # kick and hihat foot close

def test_exclude_pitches():
    print("///////////////////////////////////////////////")
    print("Testing exclude_pitches...")

    mid = mido.MidiFile(MIDI_FILE)
    oldTrack = mid.tracks[0]

    att = AbsoluteTimeTrack(oldTrack)
    newTrack = att.getMidiTrackExcludingPitches(TEST_PITCHES)

    mid.tracks[0] = newTrack
    mid.save(EXCLUDE_OUT)
    print(f"test_exclude_pitches output must be inspected manually.")
    print(f"Saved to {EXCLUDE_OUT}")

def test_exclude_pitches_no_changes():
    print("///////////////////////////////////////////////")
    print("Testing exclude_pitches_no_changes...")

    mid = mido.MidiFile(MIDI_FILE)
    oldTrack = mid.tracks[0]
    
    att = AbsoluteTimeTrack(oldTrack)
    newTrack = att.getMidiTrackExcludingPitches([])
    
    assert(len(newTrack) == len(oldTrack)), f"Unchanged track is not the same length as original. length oldTrack: {oldTrack}, length of newTrack: {newTrack}"
    print(f"Lengths of tracks are the same. Length: {len(newTrack)}")
    
    for i in range(5):
        # pick a random message, make sure they have the same time
        ix = random.randint(0, len(oldTrack))
        oldM = oldTrack[ix]
        newM = newTrack[ix]

        assert(oldM.time == newM.time), f"Message time at index {ix} is not the same between tracks. oldM time: {oldM.time}, newM time: {newM.time}"
        print(f"Message times are the same. Time: {oldM.time}")

    print("to_MidiTrack_no_changes tests passed!")

def test_include_pitches():
    print("///////////////////////////////////////////////")
    print("Testing include_pitches...")

    mid = mido.MidiFile(MIDI_FILE)
    oldTrack = mid.tracks[0]

    att = AbsoluteTimeTrack(oldTrack)
    newTrack = att.getMidiTrackIncludingPitches(TEST_PITCHES)

    mid.tracks[0] = newTrack
    mid.save(INCLUDE_OUT)
    print(f"test_include_pitches output must be inspected manually.")
    print(f"Saved to {INCLUDE_OUT}")

def test_merge_absolute_time_tracks():
    print("///////////////////////////////////////////////")
    print("Testing merge_absolute_time_tracks...")

    mid1 = mido.MidiFile(MERGEE_1)
    mid2 = mido.MidiFile(MERGEE_2)

    att1 = AbsoluteTimeTrack(mid1.tracks[0])
    att2 = AbsoluteTimeTrack(mid2.tracks[0])

    mergedAtt = AbsoluteTimeTrack.mergeAbsoluteTimeTracks(att1, att2)
    
    assert len(mergedAtt) == len(att1) + len(att2) - 1, f"Length of merged absolute time track is not the sum of the lengths of the two tracks minus 1. Length of mergedAtt: {len(mergedAtt)}, length of att1: {len(att1)}, length of att2: {len(att2)}"
    print(f"Length of merged absolute time track is correct. Length: {len(mergedAtt)}")
    
    mid1.tracks[0] = mergedAtt.toMidiTrack()
    mid1.save(SIMPLE_MERGED_OUT)
    print(f"test_merge_absolute_tracks must be inspected manually.")
    print(f"Saved to {SIMPLE_MERGED_OUT}")

def test_merge_absolute_time_tracks_one_empty():
    print("///////////////////////////////////////////////")
    print("Testing merge_absolute_time_tracks_one_empty...")

    mid = mido.MidiFile(MERGEE_1)
    att = AbsoluteTimeTrack(mid.tracks[0])
    mergedAtt = AbsoluteTimeTrack.mergeAbsoluteTimeTracks(att, AbsoluteTimeTrack())

    assert len(mergedAtt) == len(att), f"Length of merged absolute time track is not the same as the length of the non-empty track. Length of mergedAtt: {len(mergedAtt)}, length of att: {len(att)}"
    print("test_merge_absolute_time_tracks_one_empty passed!")

def test_get_note_messages_abs_track():
    print("///////////////////////////////////////////////")
    print("Testing get_note_messages_abs_track...")

    mid = mido.MidiFile(MERGEE_1)
    att = AbsoluteTimeTrack(mid.tracks[0])
    noteAtt = AbsoluteTimeTrack.getNoteMessagesAbsTrack(att, True)
    assert len(noteAtt) > 2, f"Length of noteAtt is less than 2. Length: {len(noteAtt)}"
    for am in noteAtt:
        m = am.msg
        assert m.type == NOTE_ON or m.type == NOTE_OFF or m.type == END_OF_TRACK, f"Message type is not note_on, note_off, or end_of_track. Message: {m}"
    print(f"test_get_note_messages_abs_track passed!") 


def test_randomly_offset_time():
    print("///////////////////////////////////////////////")
    print("Testing randomly_offset_time...")

    mid = mido.MidiFile(MERGEE_3)
    att = AbsoluteTimeTrack(mid.tracks[0])
    offsetAmount = 10
    originalNoteAtt = AbsoluteTimeTrack.getNoteMessagesAbsTrack(att, True)
    offsetNoteAtt = AbsoluteTimeTrack.randomlyOffsetTime(originalNoteAtt, offsetAmount)

    assert len(originalNoteAtt) == len(offsetNoteAtt), f"Length of noteAtt is not the same as the length of offsetNoteAtt. Length of noteAtt: {len(originalNoteAtt)}, length of offsetNoteAtt: {len(offsetNoteAtt)}"
    for i in range(len(offsetNoteAtt)):
        offsetTime = offsetNoteAtt[i].absTime
        originalTime = originalNoteAtt[i].absTime
        assert (offsetTime <= (originalTime + offsetAmount)) and (offsetTime >= (originalTime - offsetAmount)), f"Offset time is not within {offsetAmount} ticks of original time. Original time: {originalTime}, offset time: {offsetTime}"
    print(f"As expected, times of offsetNoteAtt are within {offsetAmount} ticks of originalNoteAtt.")

    track = offsetNoteAtt.toMidiTrack()
    mid.tracks[0] = track
    mid.save(OFFSET_TIME_OUT)
    print(f"test_randomly_offset_time output must be inspected manually.")


def test_randomly_offset_velocities():
    print("///////////////////////////////////////////////")
    print("Testing randomly_offset_velocities...")
    mid = mido.MidiFile(MERGEE_3)
    att = AbsoluteTimeTrack(mid.tracks[0])
    offsetAmount = 10
    originalNoteAtt = AbsoluteTimeTrack.getNoteMessagesAbsTrack(att, True)
    offsetNoteAtt = AbsoluteTimeTrack.randomlyOffsetVelocities(originalNoteAtt, offsetAmount)

    assert len(originalNoteAtt) == len(offsetNoteAtt), f"Length of noteAtt is not the same as the length of offsetNoteAtt. Length of noteAtt: {len(originalNoteAtt)}, length of offsetNoteAtt: {len(offsetNoteAtt)}"
    for i in range(len(offsetNoteAtt)):
        if isinstance(offsetNoteAtt[i].msg, mido.Message):
            offsetVelocity = offsetNoteAtt[i].msg.velocity
            originalVelocity = originalNoteAtt[i].msg.velocity
            assert (offsetVelocity <= (originalVelocity + offsetAmount)) and (offsetVelocity >= (originalVelocity - offsetAmount)), f"Offset velocity is not within {offsetAmount} ticks of original velocity. Original velocity: {originalVelocity}, offset velocity: {offsetVelocity}"
    print(f"As expected, velocities of offsetNoteAtt are within {offsetAmount} ticks of originalNoteAtt.")

    track = offsetNoteAtt.toMidiTrack()
    mid.tracks[0] = track
    mid.save(OFFSET_VELOCITY_OUT)
    print(f"test_randomly_offset_velocities output must be inspected manually.")


if __name__ == '__main__':
    clearOutputDir(OUTPUT_DIR)
    random.seed = SEED

    test_exclude_pitches()
    test_exclude_pitches_no_changes()
    test_include_pitches()
    test_merge_absolute_time_tracks()
    test_merge_absolute_time_tracks_one_empty()
    test_get_note_messages_abs_track()
    test_randomly_offset_time()
    test_randomly_offset_velocities()