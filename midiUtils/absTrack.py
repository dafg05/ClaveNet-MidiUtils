from midiUtils.constants import *

import mido
import copy
import random

class AbsoluteTimeMidiMessage():
    """
    A container object for midiMessages and their absolute time.
    Works with copies of mido.MidiMessages, not the original.
    """
    def __init__(self, msg: mido.Message, absTime: int):
        self.msg = copy.deepcopy(msg)
        self.absTime = absTime

class AbsoluteTimeTrack():
    """
    Like a mido.MidiTrack, but stores the absolute time of each message in adddition to the message itself.
    """
    def __init__(self, track: mido.MidiTrack = []):
        # List of AbsoluteTimeMidiMessages
        self._absTimeMsgs = []

        currAbsTime = 0
        for msg in track:
            currAbsTime += msg.time
            self._absTimeMsgs.append(AbsoluteTimeMidiMessage(msg, currAbsTime))
    
    def append(self, am: AbsoluteTimeMidiMessage):
        if len(self._absTimeMsgs) > 0:
            assert(am.absTime >= self._absTimeMsgs[-1].absTime), f"AbsoluteTimeMidiMessage to append has absTime {am.absTime}, which is less than the last message's absTime {self._absTimeMsgs[-1].absTime}"
        self._absTimeMsgs.append(am)

    def getEndOfTrackIndices(self) -> list:
        """
        Returns a list of indices of end of track messages.
        """
        eot_ixs = []
        for i, am in enumerate(self._absTimeMsgs):
            if am.msg.type == END_OF_TRACK:
                eot_ixs.append(i)
        return eot_ixs

    def toMidiTrack(self) -> mido.MidiTrack:
        """
        Using only the absTime field in AbsoluteTimeMidiMessage, create a mido.MidiTrack.
        This means that we ignore the value msg.time, and instead use the absTime field.
        """
        track = mido.MidiTrack()
        previousAbsTime = 0
        for am in self._absTimeMsgs:
            # compute deltaTime, assign it to each MidiMessage's time field
            delta_time = am.absTime - previousAbsTime
            am.msg.time = delta_time
            track.append(am.msg)
            previousAbsTime = am.absTime
        return track
    
    def __getitem__(self, index_or_slice):
        return self._absTimeMsgs[index_or_slice]
    
    def __setitem__(self, index, value):
        raise Exception("AbsoluteTimeTrack does not support __setitem__")
    
    def __len__(self):
        return len(self._absTimeMsgs)
    
    def __iter__(self):
        return iter(self._absTimeMsgs)
    
    def __repr__(self):
        return f"AbsoluteTimeTrack({self._absTimeMsgs})"
    
    def pop(self, index=-1):
        return self._absTimeMsgs.pop(index)
       
def getMidiTrackExcludingPitches(absTrack: AbsoluteTimeTrack, pitches: list) -> mido.MidiTrack:
    """
    Construct a midiTrack. Any messages whose pitch is contained in the given list of pitches will not be included.
    """
    def shouldBeRemoved(msg: mido.Message) -> bool:
        """
        Determines if a midi message should be excluded from the new track based on its pitch.
        """
        if isinstance(msg, mido.Message):
            if m.type == NOTE_ON or m.type == NOTE_OFF:
                if m.note in pitches:
                    return True
            return False

    newAbsTrack = AbsoluteTimeTrack()
    for am in absTrack:
        m = am.msg
        if not shouldBeRemoved(m):
            newAbsTrack.append(am)

    return newAbsTrack.toMidiTrack()

def getNoteMessagesAbsTrack(absTrack: AbsoluteTimeTrack, includeEndOfTrack: bool) -> AbsoluteTimeTrack:
    """
    Return a new AbsoluteTimeTrack containing only note_on and note_off messages (and end of track, if specified)
    """
    noteAbsTrack = AbsoluteTimeTrack()
    for am in absTrack:
        m = am.msg
        if m.type == NOTE_ON or m.type == NOTE_OFF or (includeEndOfTrack and m.type == END_OF_TRACK):
            noteAbsTrack.append(am)
    return noteAbsTrack

def getMidiTrackIncludingPitches(absTrack: AbsoluteTimeTrack, pitches: list) -> mido.MidiTrack:
    """
    Construct a midiTrack with only the pitches in the given list.
    """
    pitchesToRemove = [x for x in range(128) if x not in pitches]
    return getMidiTrackExcludingPitches(absTrack, pitchesToRemove)

def mergeAbsoluteTimeTracks(absTrack1: AbsoluteTimeTrack, absTrack2: AbsoluteTimeTrack) -> AbsoluteTimeTrack:
    """
    Merge absolute time tracks, preserving the order of messages, with some tie breaking rules.
    Keep the end of track with the largest absolute time.
    """

    if len(absTrack1) == 0:
        return absTrack2
    if len(absTrack2) == 0:
        return absTrack1

    # meat of the track merging algorithm
    newAbsTrack = AbsoluteTimeTrack()
    i, j = 0, 0
    while i < len(absTrack1) and j < len(absTrack2):
        if absTrack1[i].absTime < absTrack2[j].absTime:
            newAbsTrack.append(absTrack1[i])
            i += 1
        elif absTrack1[i].absTime == absTrack2[j].absTime:
            # tie breaking: end of track messages should always go second.
            # barring that, note_off messages should go first
            # otherwise, prioritize the first track
            m1 = absTrack1[i].msg
            m2 = absTrack2[j].msg

            if m1.type == END_OF_TRACK:
                newAbsTrack.append(absTrack2[j])
                j += 1
            elif m2.type == END_OF_TRACK:
                newAbsTrack.append(absTrack1[i])
                i += 1
            elif m2.type == NOTE_OFF:
                newAbsTrack.append(absTrack2[j])
                j += 1
            else:
                newAbsTrack.append(absTrack1[i])
                i += 1
        else:
            newAbsTrack.append(absTrack2[j])
            j += 1
    # append the rest of the messages
    while i < len(absTrack1):
        newAbsTrack.append(absTrack1[i])
        i += 1
    while j < len(absTrack2):
        newAbsTrack.append(absTrack2[j])
        j += 1
    
    # remove the first end of track message, since we only want one
    eot_ixs = newAbsTrack.getEndOfTrackIndices()
    if len(eot_ixs) > 1:
        newAbsTrack.pop(eot_ixs[0])
    return newAbsTrack

# TESTS
def _test_exclude_pitches():
    mid = mido.MidiFile(TEST_MIDI_FILE)
    oldTrack = mid.tracks[0]

    att = AbsoluteTimeTrack(oldTrack)
    newTrack = getMidiTrackExcludingPitches(att, TEST_PITCHES)

    mid.tracks[0] = newTrack
    mid.save(TEST_EXCLUDE_OUT)
    print(f"_test_exclude_pitches must be inspected manually.")
    print(f"Saved to {TEST_EXCLUDE_OUT}")

def _test_exclude_pitches_no_changes():
    mid = mido.MidiFile(TEST_MIDI_FILE)
    oldTrack = mid.tracks[0]
    
    att = AbsoluteTimeTrack(oldTrack)
    newTrack = getMidiTrackExcludingPitches(att, [])
    
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

def _test_include_pitches():
    mid = mido.MidiFile(TEST_MIDI_FILE)
    oldTrack = mid.tracks[0]

    att = AbsoluteTimeTrack(oldTrack)
    newTrack = getMidiTrackIncludingPitches(att, TEST_PITCHES)

    mid.tracks[0] = newTrack
    mid.save(TEST_INCLUDE_OUT)
    print(f"_test_include_pitches must be inspected manually.")
    print(f"Saved to {TEST_INCLUDE_OUT}")

def _test_merge_absolute_time_tracks():
    mid1 = mido.MidiFile(TEST_MERGEE_1)
    mid2 = mido.MidiFile(TEST_MERGEE_2)

    att1 = AbsoluteTimeTrack(mid1.tracks[0])
    att2 = AbsoluteTimeTrack(mid2.tracks[0])

    mergedAtt = mergeAbsoluteTimeTracks(att1, att2)
    
    assert len(mergedAtt) == len(att1) + len(att2) - 1, f"Length of merged absolute time track is not the sum of the lengths of the two tracks minus 1. Length of mergedAtt: {len(mergedAtt)}, length of att1: {len(att1)}, length of att2: {len(att2)}"
    print(f"Length of merged absolute time track is correct. Length: {len(mergedAtt)}")
    
    mid1.tracks[0] = mergedAtt.toMidiTrack()
    mid1.save(TEST_SIMPLE_MERGED_OUT)
    print(f"_test_merge_absolute_tracks must be inspected manually.")
    print(f"Saved to {TEST_SIMPLE_MERGED_OUT}")

def _test_merge_absolute_time_tracks_one_empty():
    mid = mido.MidiFile(TEST_MERGEE_1)
    att = AbsoluteTimeTrack(mid.tracks[0])
    mergedAtt = mergeAbsoluteTimeTracks(att, AbsoluteTimeTrack())

    assert len(mergedAtt) == len(att), f"Length of merged absolute time track is not the same as the length of the non-empty track. Length of mergedAtt: {len(mergedAtt)}, length of att: {len(att)}"
    print(f"Length of merged absolute time track is correct. Length: {len(mergedAtt)}")

def _test_get_note_messages_abs_track():
    mid = mido.MidiFile(TEST_MERGEE_1)
    att = AbsoluteTimeTrack(mid.tracks[0])
    noteAtt = getNoteMessagesAbsTrack(att, True)
    assert len(noteAtt) > 2, f"Length of noteAtt is less than 2. Length: {len(noteAtt)}"
    for am in noteAtt:
        m = am.msg
        assert m.type == NOTE_ON or m.type == NOTE_OFF or m.type == END_OF_TRACK, f"Message type is not note_on, note_off, or end_of_track. Message: {m}"
    print(f"_test_get_note_messages_abs_track passed!")

if __name__ == '__main__':
    _test_exclude_pitches_no_changes()
    _test_exclude_pitches()
    _test_include_pitches()
    _test_merge_absolute_time_tracks()
    _test_merge_absolute_time_tracks_one_empty()
    _test_get_note_messages_abs_track()