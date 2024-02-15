from midiUtils.constants import *
from midiUtils import tools
from midiUtils.augExamples import SeedExamplesRetriever
from typing import List, Tuple

import mido
import copy
import numpy as np

            
def transformMidiFile(mid: mido.MidiFile, trackIndex: int, numReplacements: int, ser: SeedExamplesRetriever, rng: np.random.Generator, preferredStyle=None, outOfStyleProb=0.0, channel=9, debug=False) -> Tuple[mido.MidiFile, List[Tuple[str, str]]]:
    """
    Transforms a midi file by probably replacing the specified voices with voices from the given style;
    otherwise replaces with voices from a different style.
    If preferred style is not specified, it will be chosen randomly from the available styles.
    params:
    - mid: the midi file to transform
    - trackIndex: the index of the track to transform
    - numReplacements: the number of voices to replace
    - ser: used to retrieve the replacement voices
    - preferredStyle: the style from which to probably choose the replacement voices. If not specified, a random style will be chosen.
    - rng: random number generator
    - outOfStyleProb: the probability of choosing a voice from a different style than the preferred style
    - channel: the channel to which the transformed track will be collapsed
    - debug: if True, prints debug information
    return: the transformed midi file and the replacement info (for each replacement track, the filename and the voice that was replaced)
    """
    if numReplacements > len(PERC_VOICES_MAPPING):
        raise ValueError(f"numReplacements cannot be greater than {len(PERC_VOICES_MAPPING)}")
    if numReplacements < 1:
        raise ValueError("numReplacements must be at least 1")

    originalTrack = mid.tracks[trackIndex]

    if preferredStyle == None:
        preferredStyle = rng.choice(ser.styles)
        
    # a list of tuples, where each tuples is structured as (noteTrack, filename, voice)
    noteTracksAndInfo = [] 
    ranOutOfCandidates = False

    for i in range(numReplacements):
        # determine whether the replacement track will be out of style
        outOfStyle = rng.random() < outOfStyleProb

        voicesReplaced = [x[2] for x in noteTracksAndInfo]
        replacementTrack, filename, voice = getReplacementTrack(preferredStyle, outOfStyle, voicesReplaced, ser, rng, debug)
        if replacementTrack == None:
            if debug:
                print(f"Ran out of candidate tracks without repeating voices for out-of-style choice '{outOfStyle}'. Iteration: {i}; voices replaced: {voicesReplaced}.")
            ranOutOfCandidates = True
            break
        noteTracksAndInfo.append((replacementTrack, filename, voice))

    # we can run out of either out-of-style or in-style tracks. If we run out of in-style tracks, we can still use out-of-style tracks, and vice versa.
    if ranOutOfCandidates:
        outOfStyle = not outOfStyle
        for j in range(i, numReplacements):
            voicesReplaced = [x[2] for x in noteTracksAndInfo]
            replacementTrack, filename, voice = getReplacementTrack(preferredStyle, outOfStyle, voicesReplaced, ser, rng, debug)
            if replacementTrack == None:
                if debug:
                    print(f"Completely ran out of candidate tracks. Iteration: {j}; Voices replaced: {voicesReplaced}.")
                break
            noteTracksAndInfo.append((replacementTrack, filename, voice))

    if debug:
        print(f"Replacing voices {voicesReplaced} with tracks from style {preferredStyle}. Out of style probability: {outOfStyleProb}")

    # delete voices to replace from original track
    voicesReplaced = [x[2] for x in noteTracksAndInfo]
    pitchesToDelete = []
    for voice in voicesReplaced:
        pitchesToDelete.extend(PERC_VOICES_MAPPING[voice])
    originalTrack = tools.deletePitches(originalTrack, pitchesToDelete)

    # merge the replacements into the original track
    noteTracks = [x[0] for x in noteTracksAndInfo]
    newTrack = tools.mergeMultipleTracks(trackWithMetaData=originalTrack, noteTracks=noteTracks)
    # collapse the track to a single channel
    newTrack = tools.allMessagesToChannel(newTrack, channel)

    # Construct transformed midi file
    transformedMid = copy.deepcopy(mid)
    transformedMid.tracks[trackIndex] = newTrack

    replacementInfo = [(x[1], x[2]) for x in noteTracksAndInfo]

    return transformedMid, replacementInfo

def getReplacementTrack(preferredStyle: str, outOfStyle: bool, voicesReplaced: List[str], ser: SeedExamplesRetriever, rng: np.random.Generator, debug=False) -> Tuple[mido.MidiTrack, str, str]:
    """
    Gets a replacement voice (midi track) using the seedExamplesRetriever.
    With a probability of (1-outOfStyleProb), the replacement voice will be from the given style.
    Given the preferredStyle and whether not we're replacing with an out of style voice, we get a list of candidate tracks, from which randomly choose one.
    We mainly return the midi track, but we also return the filename and the voice of the chosen track so that we can keep track of which voices have been replaced by what track.
    """

    candidatesInfo = ser.getCandidateTracksInfo(preferredStyle, outOfStyle, voicesToExclude=voicesReplaced)
    if not candidatesInfo:
        return None, None, None
    filename, voice = rng.choice(candidatesInfo)
    if debug:
        print(f"Chose track from {filename} with voice {voice} to replace. Out of style? {outOfStyle}")
    return ser.getTrack(filename, voice), filename, voice