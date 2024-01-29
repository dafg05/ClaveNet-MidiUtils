import mido
import copy

NOTE_ON = 'note_on'
NOTE_OFF = 'note_off'

class AbsoluteTimeMidiMessage():
    """
    A container object for midiMessages and their absolute time.
    Works with copies of mido.MidiMessages, not the original.
    """
    def __init__(self, msg: mido.Message, absTime: int):
        self.msg = copy.deepcopy(msg)
        self.absTime = absTime

class AbsoluteTimeMidiTrack():
    """
    An object that contains a list of absMidiMessages.
    Essentially the same as a mido.MidiTrack, but has contains the absolute time field as well.

    To mutate the absTimeMsgs, we can modify its elements, append to it and delete it as a list.
    However, in order to safely convert back to mido.MidiTrack(), make sure to use the toMidiTrack() method.
    """
    def __init__(self, track: mido.MidiTrack):
        self._absTimeMsgs = []

        currAbsTime = 0
        for msg in track:
            currAbsTime += msg.time
            self._absTimeMsgs.append(AbsoluteTimeMidiMessage(msg, currAbsTime))

    @staticmethod
    def toMidiTrack(absTimeMsgs) -> mido.MidiTrack:
        """
        Using only the absTime field in AbsoluteTimeMidiMessage, create a mido.MidiTrack.
        This means that we ignore the value msg.time, and instead use the absTime field.
        TODO: test me
        """
        track = mido.MidiTrack()
        previousAbsTime = 0
        for am in absTimeMsgs:
            # compute deltaTime, assign it to each MidiMessage's time field
            delta_time = am.absoluteTime - previousAbsTime
            am.msg.time = delta_time
            track.append(am.msg)
            previousAbsTime = am.absoluteTime
        return track
    
    def getTrackExcludingPitches(self, pitches: list) -> mido.MidiTrack:
        """
        Construct a midiTrack. Any messages whose pitch is contained in the given list of pitches will not be included.
        TODO: test me
        """
        def shouldBeRemoved(msg: mido.Message) -> bool:
            """
            Determines if a midi message should be excluded from the new track based on its pitch.
            """
            if m.type == NOTE_ON or NOTE_OFF:
                if m.note in pitches:
                    return True
            return False

        newAbsTimeMsgs = []
        for am in self._absTimeMsgs:
            m = am.msg
            if not shouldBeRemoved(m):
                newAbsTimeMsgs.append(am)

        return AbsoluteTimeMidiTrack.toMidiTrack(newAbsTimeMsgs)
    
    def getTrackIncludingPitches(self, pitches: list) -> mido.MidiTrack:
        """
        Construct a midiTrack with only the pitches in the given list.
        """
        pitchesToRemove = [x for x in range(128) if x not in pitches]
        return self.getTrackExcludingPitches(pitchesToRemove)




        
