from midiUtils.constants import *

import math
import mido
import os

def splitMidiTrackIntoBars(track: mido.MidiTrack, barStep: int, beatsPerBar: int,  ticksPerBeat: int):
    metaData = getBeginningMetaData(track)
    
    midiSlicesTracks = []
    totalSlices = getTotalSlices(track, barStep, beatsPerBar, ticksPerBeat)
    sliceLen = ticksPerBeat * barStep * beatsPerBar

    firstSlice = True
    for startTime in range(0, sliceLen * totalSlices, sliceLen):
        endTime = startTime + sliceLen
        if firstSlice: # first slice does not need meta data
            midiSliceTrack = getMidiSlice(track, startTime, endTime)
            firstSlice = False
        else:
            midiSliceTrack = getMidiSlice(track, startTime, endTime, metaData)
        midiSlicesTracks.append(midiSliceTrack)
    
    return midiSlicesTracks

def trimMidiTrack(track: mido.MidiTrack, startBar: int, endBar: int, beatsPerBar: int, ticksPerBeat: int):
    metaData = getBeginningMetaData(track)

    startTime = startBar * beatsPerBar * ticksPerBeat
    endTime = endBar * beatsPerBar * ticksPerBeat
    return getMidiSlice(track, startTime, endTime, metaData)

def getMidiSlice(track: mido.MidiTrack, startTime: int, endTime, metaData: list = None):
    """Extracts midi events from startTime to endTime into a new track
    
    :param track: the midi track to slice
    :param startTime: tick where slice begins
    :param endTime: tick where slice ends
    :optional param metaData: list of meta messages that occur before the first non-meta message

    :returns newTrack: new midi track containing events from startTime to endTime
    """

    def firstMessageInSlice(startTime: int):
        """
        Returns index of first message that occurs after startTime
        Also returns the absoluteTimeOfFirstMessage - startTime as firstMssgTime
        """
        firstMssgIndex = 0
        absTime = track[firstMssgIndex].time
        while not (absTime >= startTime):
            firstMssgIndex += 1
            if firstMssgIndex < len(track):
                absTime += track[firstMssgIndex].time
            else:
                return -1, -1
        firstMssgTime = absTime - startTime
        return firstMssgIndex, firstMssgTime
    
    # PRELIMINARY CALCULATIONS ---------------------------------------------

    # get index of first message that occurs after startTime
    messageIndex, firstMssgTime = firstMessageInSlice(startTime)
    # if messageIndex is -1 or it exceeds the len of the track, then there are no messages within this midi slice
    if messageIndex == -1 or messageIndex == len(track):
        return mido.MidiTrack()

    # MAIN ALGORITHM -------------------------------------------------------

    # initialize new track
    newTrack = mido.MidiTrack()
    if metaData:
        newTrack.extend(metaData)
    absTime = startTime

    # noteOnArray: indices are note values
    # value is either -1 if note is off, channelNum if note is on
    # we'll need the channelNum to turn any hanging notes off
    noteOnArray = [-1 for x in range(128)]

    firstMessage = track[messageIndex]
    message = firstMessage.copy()
    # due to delta time, change the first message time to be played  after the midi slice starts
    message.time = firstMssgTime
    absTime += message.time # absolute time of current message

    # main loop ---
    while absTime < endTime:
        # if absTime is within the midi slice, copy it to new track
        newTrack.append(message)

        # bookkeeping for noteOnArray
        if (isinstance(message, mido.Message)):
            if message.type == 'note_on':
                noteOnArray[message.note] = message.channel
            elif message.type == 'note_off':
                noteOnArray[message.note] = -1
        
        messageIndex += 1
        if messageIndex == len(track):
            break
        message = track[messageIndex]
        absTime += message.time
    # --- end loop

    def closeMidiTrack(track: mido.MidiTrack):
        """
        Append noteOffs if noteOns were left hanging, append endOfTrack metaMessage.
        Modifies midi track in place
        """
        # note offs
        hangingNotes = [i for i, noteOn in enumerate(noteOnArray) if noteOn >= 0]

        firstNoteOff = True
        for note in hangingNotes:
            if firstNoteOff:
                # set the first note off message absolute time at end time - 1. 
                # all additional offs should have the same absolute time
            
                lastMessageAbsTime = (absTime - message.time)    
                noteOffTime = (endTime - 1) - lastMessageAbsTime
                firstNoteOff = False
            else:
                noteOffTime = 0
            track.append(mido.Message('note_off', note=note, velocity=64, time=noteOffTime, channel=noteOnArray[note]))

        # end of track meta message, if needed
        if track[-1].type != 'end_of_track':
            track.append(mido.MetaMessage('end_of_track'))
    
    # clean up track
    closeMidiTrack(newTrack)
    return newTrack

def getTrackWithSelectPitches(track: mido.MidiTrack, pitches: list):
    """
    Returns a midi track that containing only the specified pitches of the original track
    """
    # initialize a new track with meta data
    newTrack = mido.MidiTrack()
    newTrack.extend(getBeginningMetaData(track))

    currAbsTime = 0
    lastAbsTime = 0
    for m in track:
        currAbsTime += m.time
        # only add messages of this specific pitch
        if isinstance(m, mido.Message) and (m.type == 'note_on' or m.type == 'note_off'):
            if m.note in pitches:
                newM = m.copy()
                newM.time = currAbsTime - lastAbsTime
                newTrack.append(newM)
                lastAbsTime = currAbsTime
    # end of track meta message
    newTrack.append(mido.MetaMessage('end_of_track'))
    return newTrack

def deletePitches(track: mido.MidiTrack, pitches: list):
    """
    Deletes all messages with the specified pitches from the track
    """
    pitchesToKeep = [x for x in range(128) if x not in pitches]
    return getTrackWithSelectPitches(track, pitchesToKeep)

def change_midi_tempo(midi_file_path, new_tempo):
    # Load the MIDI file
    mid = mido.MidiFile(midi_file_path)

    # Create a new MIDI file with the adjusted tempo
    new_mid = mido.MidiFile()
    new_track = mido.MidiTrack()
    new_mid.tracks.append(new_track)

    for msg in mid.tracks[0]:
        # If we find a set_tempo message, change its tempo
        if msg.type == 'set_tempo':
            msg = mido.MetaMessage('set_tempo', tempo=new_tempo)
        new_track.append(msg)

    # Save the new MIDI file
    new_mid.save(midi_file_path)

    return midi_file_path


def getBeginningMetaData(track: mido.MidiTrack):
    """
    Returns a list of meta messages that occur before the first non-meta message
    """
    metaData = []
    if len(track) == 0:
        return []
    i = 0
    while isinstance(track[i], mido.MetaMessage):
        if track[i].time != 0:
            raise Exception(f"MetaDataMessage's time is not 0. {track[i]}")
        metaData.append(track[i])
        i += 1
    return metaData

def getTrackWithoutBeginningMetaData(track: mido.MidiTrack):
    """
    Returns a track without the meta messages that occur before the first non-meta message
    """
    i = 0
    while isinstance(track[i], mido.MetaMessage):
        i += 1
    return track[i:]

def mergeTracks(track1, track2):
    """
    Merge two midi tracks; aka combines the messages of both tracks into a single track.
    Keeps track1's metadata
    """
    def getMidiMessages(track, withMetaData):
        """
        returns the midi messages of a track as a list of tuples (absoluteTime, message)
        """
        absoluteTime = 0
        trackEvents = []
        for msg in track:
            if isinstance(msg, mido.MetaMessage):
                if withMetaData:
                    trackEvents.append((absoluteTime, msg))
                # Stop collecting meta messages after the first non-meta message.
                withMetaData = not isinstance(msg, mido.Message)
            else:
                absoluteTime += msg.time
                trackEvents.append((absoluteTime, msg))
        return trackEvents

    def mergeSortedEvents(events1, events2):
        mergedEvents = []
        i, j = 0, 0

        while i < len(events1) and j < len(events2):
            if events1[i][0] <= events2[j][0]:
                mergedEvents.append(events1[i])
                i += 1
            else:
                mergedEvents.append(events2[j])
                j += 1
        
        # Add any remaining events from either list
        mergedEvents.extend(events1[i:])
        mergedEvents.extend(events2[j:])
        return mergedEvents

    events1 = getMidiMessages(track1, withMetaData=True)
    events2 = getMidiMessages(track2, withMetaData=False)

    mergedEvents = mergeSortedEvents(events1, events2)

    mergedTrack = mido.MidiTrack()
    lastTime = 0
    for absoluteTime, msg in mergedEvents:
        deltaTime = absoluteTime - lastTime
        lastTime = absoluteTime
        newMsg = msg.copy(time=deltaTime)
        mergedTrack.append(newMsg)

    return mergedTrack

def mergeMultipleTracks(tracks: list):
    """
    Merges multiple tracks into a single track
    """
    # mergedTrack = MidiTrack()
    mergedTrack = tracks[0]
    for track in tracks:
        mergedTrack = mergeTracks(mergedTrack, track)
    return mergedTrack

def concatenateTracks(track1: mido.MidiTrack, track2: mido.MidiTrack):
    """
    Concatenates track2 to the end of track1. Keeps track1 metadata
    """
    newTrack = mido.MidiTrack()
    newTrack.extend(track1)
    # remove last element, which is an end of track element from track1.
    newTrack.pop()
    # concatenate track 2, removing its beginning metadata
    newTrack.extend(getTrackWithoutBeginningMetaData(track2))
    # add end of track message
    newTrack.append(mido.MetaMessage('end_of_track'))
    return newTrack

def concatenateMidiFiles(sourceDir: str, outputDir: str):
    """
    Concatenates all midi files in midiDir into a single midi file
    """
    files = [f for f in os.listdir(sourceDir) if ".mid" in f]
    firstMid = mido.MidiFile(f"{sourceDir}/{files[0]}")
    concatTrack = getBeginningMetaData(firstMid.tracks[0])
    for f in files:
        mid = mido.MidiFile(f"{sourceDir}/{f}")
        concatTrack = concatenateTracks(concatTrack, mid.tracks[0])
    concatTrack.append(mido.MetaMessage('end_of_track'))
    
    newMid = mido.MidiFile(ticks_per_beat=firstMid.ticks_per_beat)
    newMid.tracks.append(concatTrack)
    newMid.save(f"{outputDir}/concatenated.mid")

def getEndTime(track: mido.MidiTrack):
    absTime = 0
    for m in track:
        absTime += m.time
    return absTime

def getPitches(percPart: str) -> list:
    """
    Returns a list of pitches that correspond to the given percPart
    Hardcoded.
    """
    if percPart == "sna":
        return SNA_NOTES
    if percPart == "toms":
        return TOM_NOTES
    if percPart == "kick":
        return KICK_NOTES
    if percPart == "cym":
        return CYM_NOTES
    return []

def isTrackEmpty(track : mido.MidiTrack):
    """
    Returns true if the track is empty, aka if it has any note on messages.
    """
    for m in track:
        if isinstance(m, mido.Message) and m.type == 'note_on':
            return False
    return True

def hasMetaData(track : mido.MidiTrack):
    """
    If the first message is a meta message of time zero, then this track contains metaData
    """
    
    message = track[0]
    if isinstance(message, mido.MetaMessage) and message.time == 0:
        return True
    return False

def getTotalSlices(track: mido.MidiTrack, barStep: int, beatsPerBar: int,  ticksPerBeat: int):
    """
    Returns the number of slices in a midi track.
    Ex: if barstep is 1, and there are four bars in the midi track, then this function returns 4
    """
    absTime = 0
    for m in track:
        absTime += m.time
    sliceLen = ticksPerBeat * barStep * beatsPerBar
    return math.ceil(absTime / sliceLen)    

if __name__ == "__main__":
    print("hello world")
