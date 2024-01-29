from midiUtils.constants import *
from midiUtils.absTrack import AbsoluteTimeTrack, AbsoluteTimeMidiMessage, getMidiTrackExcludingPitches, getMidiTrackIncludingPitches, mergeAbsoluteTimeTracks, getNoteMessagesAbsTrack

import math
import mido
import os

def splitMidiTrackIntoBars(track: mido.MidiTrack, barStep: int, beatsPerBar: int,  ticksPerBeat: int):
    """
    TODO: refactor to use absTrack
    """
    metaData = getMetaDataAndIndex(track)
    
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
    """
    TODO: refactor to use absTrack
    """
    metaData = getMetaDataAndIndex(track)

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

    TODO: refactor to use absTrack
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
        if track[-1].type != END_OF_TRACK:
            track.append(mido.MetaMessage(END_OF_TRACK))
    
    # clean up track
    closeMidiTrack(newTrack)
    return newTrack

def getTrackWithSelectPitches(track: mido.MidiTrack, pitches: list) -> mido.MidiTrack:
    """
    Returns a midi track that containing only the specified pitches of the original track
    """
    trackTools = AbsoluteTimeTrack(track)
    return trackTools.getTrackIncludingPitches(pitches)

def deletePitches(track: mido.MidiTrack, pitches: list):
    """
    Deletes all messages with the specified pitches from the track
    """
    trackTools = AbsoluteTimeTrack(track)
    return trackTools.getTrackExcludingPitches(pitches)

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


def getMetaDataAndIndex(track: mido.MidiTrack):
    """
    Teturn metadata as a list of messages, AND the index of the first non-metadata message.
    We assume that a track's metaData is the collection of metaMessages that occur before the first non-meta message, excluding the end of track message.
    """
    if len(track) == 0:
        return []
    
    metaData = []
    i = 0
    while isinstance(track[i], mido.MetaMessage) and track[i].time == 0:
        # if we encounter an end of track message, return the metaData
        if track[i].type == END_OF_TRACK:
            break
        metaData.append(track[i])
        if i + 1 == len(track):
            break
        i += 1
    return metaData, i

def getTrackWithoutBeginningMetaData(track: mido.MidiTrack):
    """
    Returns a track without the meta messages that occur before the first non-meta message
    """
    _, i = getMetaDataAndIndex(track)
    return track[i:]

def mergeMultipleTracks(trackWithMetaData, noteTracks) -> mido.MidiTrack:
    """
    Merges tracks into a single track, fixing all messages to the same channel.
    The metadata in trackWithMetaData will be used for the final merged track.
    For note tracks, all messages other than note_on or note_off will be skipped.
    """
    mergedAbsTrack = AbsoluteTimeTrack(trackWithMetaData)
    for noteTrack in noteTracks:
        noteAbsTrack = AbsoluteTimeTrack(noteTrack)
        noteAbsTrack = getNoteMessagesAbsTrack(noteAbsTrack, includeEndOfTrack=True)
        mergedAbsTrack = mergeAbsoluteTimeTracks(mergedAbsTrack, noteAbsTrack)
    return mergedAbsTrack.toMidiTrack()

def allMessagesToChannel(track: mido.MidiTrack, channel: int):
    """
    Changes the channel of all messages in the track to the given channel
    """
    for msg in track:
        if isinstance(msg, mido.Message):
            msg.channel = channel

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
    newTrack.append(mido.MetaMessage(END_OF_TRACK))
    return newTrack

def concatenateMidiFiles(sourceDir: str, outputDir: str):
    """
    Concatenates all midi files in midiDir into a single midi file
    """
    files = [f for f in os.listdir(sourceDir) if ".mid" in f]
    firstMid = mido.MidiFile(f"{sourceDir}/{files[0]}")
    concatTrack = getMetaDataAndIndex(firstMid.tracks[0])
    for f in files:
        mid = mido.MidiFile(f"{sourceDir}/{f}")
        concatTrack = concatenateTracks(concatTrack, mid.tracks[0])
    concatTrack.append(mido.MetaMessage(END_OF_TRACK))
    
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
    If the first message of a track is a meta message of time zero, then this track contains metaData
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
