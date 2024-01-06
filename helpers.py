from constants import *

import math
import mido

def splitMidiTrackIntoBars(track: mido.MidiTrack, barStep: int, beatsPerBar: int,  ticksPerBeat: int):
    metaData = getBeginningMetaData(track)
    
    midiSlicesTracks = []
    totalSlices = getTotalSlices(track, barStep, beatsPerBar, ticksPerBeat)
    sliceLen = ticksPerBeat * barStep * beatsPerBar

    for startTime in range(0, sliceLen * totalSlices, sliceLen):
        endTime = startTime + sliceLen
        midiSliceTrack = getMidiSlice(track, startTime, endTime, metaData)
        midiSlicesTracks.append(midiSliceTrack)
    
    return midiSlicesTracks


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


def getMidiSlice(track: mido.MidiTrack, startTime: int, endTime, metaData: list = []):
    """Extracts midi events from startTime to endTime into a new track
    
    :param track: the midi track to slice
    :param startTime: tick where slice begins
    :param endTime: tick where slice ends
    :optional param metaData: list of meta messages that occur before the first non-meta message

    :returns newTrack: new midi track containing events from startTime to endTime
    """

    def firstMessageInSlice(startTime: int):
        """
        Returns index of first message (non-meta) that occurs after startTime
        Also returns the time the first message time (adjusted for startTime)
        """
        firstMssgIndex = 0
        absTime = track[firstMssgIndex].time
        # exclude meta messages within time slice
        while not (absTime >= startTime and isinstance(track[firstMssgIndex], mido.Message)):
            firstMssgIndex += 1
            if firstMssgIndex < len(track):
                absTime += track[firstMssgIndex].time
            else:
                return -1
        firstMssgTime = absTime - startTime
        return firstMssgIndex, firstMssgTime
    
    # PRELIMINARY CALCULATIONS ---------------------------------------------

    # get index of first message that occurs after startTime
    messageIndex, firstMssgTime = firstMessageInSlice(startTime)
    # if messageIndex is -1 or it exceeds the len of the track, then there are no messages within this midi slice
    if messageIndex == -1 or messageIndex == len(track):
        return mido.MidiTrack()
    
    # calculate metaData if it wasn't provided
    if metaData == []:
        metaData = getBeginningMetaData(track)

    # MAIN ALGORITHM -------------------------------------------------------

    # initialize new track with metadata
    newTrack = mido.MidiTrack()
    newTrack.extend(metaData)
    absTime = startTime

    # indices are note values
    # value is either -1 if note is off, channelNum if note is on
    # we'll need the channelNum to turn any hanging notes off
    noteOnArray = [-1 for x in range(128)]

    firstMessage = track[messageIndex]
    message = firstMessage.copy()
    # due to delta time, change the first message time to be played  after the midi slice starts
    message.time = firstMssgTime
    absTime += message.time# absolute time of current message

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

        if len(hangingNotes) == 0:
            # set end of track absolute time to be at end time
            lastMessageAbsTime = (absTime - message.time)
            endOfTrackTime = (endTime - 1) - lastMessageAbsTime
            
            eotMessage = mido.MetaMessage('end_of_track')
            eotMessage.time = endOfTrackTime
            
            track.append(eotMessage)
        
        else:
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

            # end of track meta message
            track.append(mido.MetaMessage('end_of_track'))
    
    # clean up track
    closeMidiTrack(newTrack)
    return newTrack

def separateIntoPitches(track: mido.MidiTrack, pitches: list):
    """
    Separates a midi track into a new track containing only the specified pitches
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
    return separateIntoPitches(track, pitchesToKeep)

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
    i = 0
    while isinstance(track[i], mido.MetaMessage):
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

def mergeTracks(trackA, trackB):
    def processTrack(track, collectMeta):
        absoluteTime = 0
        trackEvents = []
        for msg in track:
            if isinstance(msg, mido.MetaMessage):
                if collectMeta:
                    trackEvents.append((absoluteTime, msg))
                # Stop collecting meta messages after the first non-meta message.
                collectMeta = not isinstance(msg, mido.Message)
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

    events1 = processTrack(trackA, collectMeta=True)
    events2 = processTrack(trackB, collectMeta=False)

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

def getEndTime(track: mido.MidiTrack):
    absTime = 0
    for m in track:
        absTime += m.time
    return absTime
        

if __name__ == "__main__":
    print("hello world")
