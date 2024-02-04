from midiUtils import helpers
from midiUtils.constants import *
from midiUtils.absTrack import AbsoluteTimeTrack

import mido
import copy

def getPitches(percVoice: str) -> list:
    """
    Returns a list of pitches that correspond to the given percVoice
    """
    if percVoice == "sna":
        return SNA_NOTES
    if percVoice == "toms":
        return TOM_NOTES
    if percVoice == "kick":
        return KICK_NOTES
    if percVoice == "cym":
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

def deletePitches(track: mido.MidiTrack, pitches: list) -> mido.MidiTrack:
    """
    Deletes all messages with the specified pitches from the track
    """
    att = AbsoluteTimeTrack(track)
    return att.getMidiTrackExcludingPitches(pitches)

def getTrackWithSelectPitches(track: mido.MidiTrack, pitches: list, notesOnly: bool=False) -> mido.MidiTrack:
    """
    Returns a midi track that containing only the specified pitches of the original track
    """
    att = AbsoluteTimeTrack(track)
    if notesOnly:
        att = AbsoluteTimeTrack.getNoteMessagesAbsTrack(att, includeEndOfTrack=True)
    return att.getMidiTrackIncludingPitches(pitches)

def mergeMultipleTracks(trackWithMetaData: mido.MidiTrack, noteTracks) -> mido.MidiTrack:
    """
    Merges tracks into a single track, fixing all messages to the same channel.
    The metadata in trackWithMetaData will be used for the final merged track.
    For note tracks, all messages other than note_on or note_off will be skipped.
    """
    mergedAbsTrack = AbsoluteTimeTrack(trackWithMetaData)
    for noteTrack in noteTracks:
        noteAbsTrack = AbsoluteTimeTrack(noteTrack)
        noteAbsTrack = AbsoluteTimeTrack.getNoteMessagesAbsTrack(noteAbsTrack, includeEndOfTrack=True)
        mergedAbsTrack = AbsoluteTimeTrack.mergeAbsoluteTimeTracks(mergedAbsTrack, noteAbsTrack)
    return mergedAbsTrack.toMidiTrack()

def trimMidiTrack(track: mido.MidiTrack, startBar: int, endBar: int, beatsPerBar: int, ticksPerBeat: int):
    """
    Trims a midi track to the specified bars.
    """
    metaData, _ = helpers.getMetaDataAndIndex(track)

    startTime = startBar * beatsPerBar * ticksPerBeat
    endTime = endBar * beatsPerBar * ticksPerBeat
    return helpers.getMidiSlice(track, startTime, endTime, metaData)

def allMessagesToChannel(track: mido.MidiTrack, channel: int) -> mido.MidiTrack:
    """
    Returns a track identical to the input track, except all messages are set to the specified channel.
    """
    newTrack = mido.MidiTrack()
    for msg in track:
        newMsg = copy.deepcopy(msg)
        if isinstance(msg, mido.Message):
            newMsg.channel = channel
        newTrack.append(newMsg)

    return newTrack