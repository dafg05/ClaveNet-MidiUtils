from __future__ import annotations
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
       
    def getMidiTrackExcludingPitches(self, pitches: list) -> mido.MidiTrack:
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
        for am in self._absTimeMsgs:
            m = am.msg
            if not shouldBeRemoved(m):
                newAbsTrack.append(am)

        return newAbsTrack.toMidiTrack()
    
    def getMidiTrackIncludingPitches(self, pitches: list) -> mido.MidiTrack:
        """
        Construct a midiTrack with only the pitches in the given list.
        """
        pitchesToRemove = [x for x in range(128) if x not in pitches]
        return self.getMidiTrackExcludingPitches(pitchesToRemove)

    @staticmethod
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

    @staticmethod
    def mergeAbsoluteTimeTracks(absTrack1: AbsoluteTimeTrack, absTrack2: AbsoluteTimeTrack) -> AbsoluteTimeTrack:
        """
        Merge absolute time tracks, preserving the order of messages, with some tie breaking rules.
        Keep the end of track with the largest absolute time.
        """
        if len(absTrack1) == 0:
            return absTrack2
        if len(absTrack2) == 0:
            return absTrack1

        def conditionalAppend(absTrack: AbsoluteTimeTrack, absTimeMsg: AbsoluteTimeMidiMessage, ix: int, foundFirstEOT: bool):
            """
            Used to make sure that we skip the first end of track message, if we haven't found it yet.
            Always increments index, but appends conditionally.
            Updates foundFirstEOT flag accordingly
            """
             # if we havent found the first end of track yet but the current message is an end of track, ignore it
            if not foundFirstEOT:
                if absTimeMsg.msg.type == END_OF_TRACK:
                    return ix + 1, True
                
            # otherwise, append and increment normally.
            absTrack.append(absTimeMsg)
            return ix + 1, foundFirstEOT

        # meat of the track merging algorithm
        newAbsTrack = AbsoluteTimeTrack()
        i, j = 0, 0
        foundFirstEOT = False
        while i < len(absTrack1) and j < len(absTrack2):
            if absTrack1[i].absTime < absTrack2[j].absTime:
                i, foundFirstEOT = conditionalAppend(newAbsTrack, absTrack1[i], i, foundFirstEOT)
            elif absTrack1[i].absTime == absTrack2[j].absTime:
                # tie breaking: end of track messages should always go second.
                # barring that, note_off messages should go first
                # otherwise, prioritize the first track
                m1 = absTrack1[i].msg
                m2 = absTrack2[j].msg

                if m1.type == END_OF_TRACK:
                    j, foundFirstEOT = conditionalAppend(newAbsTrack, absTrack2[j], j, foundFirstEOT)
                elif m2.type == END_OF_TRACK:
                    i, foundFirstEOT = conditionalAppend(newAbsTrack, absTrack1[i], i, foundFirstEOT)
                elif m2.type == NOTE_OFF:
                    j, foundFirstEOT = conditionalAppend(newAbsTrack, absTrack2[j], j, foundFirstEOT)
                else:
                    i, foundFirstEOT = conditionalAppend(newAbsTrack, absTrack1[i], i, foundFirstEOT)
            else:
                j, foundFirstEOT = conditionalAppend(newAbsTrack, absTrack2[j], j, foundFirstEOT)

        # append the rest of the messages
        while i < len(absTrack1):
            i, foundFirstEOT = conditionalAppend(newAbsTrack, absTrack1[i], i, foundFirstEOT)
        while j < len(absTrack2):
            j, foundFirstEOT = conditionalAppend(newAbsTrack, absTrack2[j], j, foundFirstEOT)
        
        return newAbsTrack
    
    @staticmethod
    def randomlyOffsetTime(noteTrack: AbsoluteTimeTrack, maxOffset: int) -> AbsoluteTimeTrack:
        """
        Asssumes that the given track is the return value of getNoteMessagesAbsTrack.
        Randomly offset the times of the note messages in the track, but caps the offset amount so that the message order is preserved.
        TODO: test me
        """
        newTrack = copy.deepcopy(noteTrack)
        for i in range(len(newTrack)):
            currAm = newTrack[i]
            if currAm.msg.type == END_OF_TRACK:
                break
            negativeOffset = random.choice([True, False])
            offsetAmount = random.randrange(0, maxOffset + 1)

            # cap the offset in either the negative or positive direction
            # to the absolute time of the previous or next message, respectively.
            if negativeOffset:
                prevMsgTime = 0 if i == 0 else newTrack[i-1].absTime # avoid a negative absolute time
                distance = abs(currAm.absTime - prevMsgTime)
                currAm.absTime -= min(offsetAmount, distance)
            else:
                # we need not worry about an index out of bounds error assuming our track has an end of time message.
                nextMsgTime = newTrack[i+1].absTime 
                distance = abs(currAm.absTime - nextMsgTime)
                currAm.absTime += min(offsetAmount, distance)

        return newTrack

    @staticmethod
    def randomlyOffsetVelocities(noteTrack: AbsoluteTimeTrack, maxOffset: int) -> AbsoluteTimeTrack:
        """
        Asssumes that the given track is the return value of getNoteMessagesAbsTrack.
        Randomly offset the velocities of the note messages in the track.
        TODO: test me
        """
        newTrack = copy.deepcopy(noteTrack)
        for am in newTrack:
            if isinstance(am.msg, mido.Message):
                am.msg.velocity += random.randrange(-maxOffset, maxOffset+1)
        return newTrack