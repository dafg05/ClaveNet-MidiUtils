from midiUtils.constants import *
from midiUtils import tools
from midiUtils.augExamples import SeedExamplesRetriever
from typing import List

import mido
import os
import random
import copy
import numpy as np

def augmentationScheme(sourceDir: str, outputDir: str, seedExamplesDir: str, styleParams: dict, suffix: int='', numTransformations: int=1, fixedVoicesToReplace: List[str]=None, numReplacements: int=1, random_seed: int=0, debug: bool=False):
    """
    For every midi file in sourceDir, computes NUM_TRANSFORMATIONS transformed midi files
    and saves them in the outputDir. 
    Note: we also write the original file to the outputDir

    param
    - sourceDir: dir that contains files to transform
    - outputDir: dir that will contain transformations + unaltered files
    - seedExamplesdir: dir that contains the seed examples to use for transformations
    - styleParams: keys are "preferredStyle" and "outOfStyleProb". 
    - sufix: to append to the output file name
    - numTransformations: number of transformations to compute for each midi file, not including the original
    - fixedVoicesToReplace: If specified, denotes the exact percussion voices that will be replaced. Else,
    voices to replace will be randomly computed.
    - ramdom_seed: random seed
    - numReplacements: If fixedVoicesToReplace is not specified, then this denotes the number of 
    randomly chosen voices to replace. Else, this parameter is ignored.
    - debug: if true, prints debug info
    """

    random.seed(random_seed)

    ser = SeedExamplesRetriever(dir=seedExamplesDir)
    for f in os.listdir(sourceDir):
        # Skip non-midi files
        if ".mid" not in f:
            continue
        mid = mido.MidiFile(f'{sourceDir}/{f}')
        mid.save(f"{outputDir}/{f}_original.mid")
        for i in range(numTransformations):
            voicesToReplace = getVoicesToReplace(fixedVoicesToReplace, numReplacements)
            trackIndex = 0

            newMid = transformMidiFile(mid, trackIndex, voicesToReplace, ser, styleParams, debug)
            newMid.save(f"{outputDir}/{f}_tra-{i:02d}{suffix}.mid")

def transformMidiFile(mid: mido.MidiFile, trackIndex: int, voicesToReplace: list, ser: SeedExamplesRetriever, styleParams: dict, debug=False) -> mido.MidiFile:
    """
    Transforms a midi file by probably replacing the specified voices with voices from the given style;
    otherwise replaces with voices from a different style.

    params
    mid: Original midifile
    trackIndex: the miditrack the replacement algorithm will be run
    voicesToReplace: strings denoting the voices that should be replaced
    ser: object to facilitate choosing replacement tracks
    styleParams: keys are "preferredStyle" and "outOfStyleProb". 

    returns
    transformedMid: transformed midiFile, which is a copy of the original save for the new track.
    """
    if debug:
        print(f"Transforming midi file {mid.filename} with voices: {voicesToReplace}, trackIndex: {trackIndex}, preferredStyle: {styleParams['preferredStyle']}, outOfStyleProb: {styleParams['outOfStyleProb']}")

    oldTrack = mid.tracks[trackIndex]
    preferredStyle = styleParams["preferredStyle"]
    outOfStyleProb = styleParams["outOfStyleProb"]

    if preferredStyle == "":
        preferredStyle = random.choice(ser.styles)

    # delete voices to replace from original track
    pitchesToDelete = []
    for voice in voicesToReplace:
        pitchesToDelete.extend(tools.getPitches(voice))
    oldTrack = tools.deletePitches(oldTrack, pitchesToDelete)

    # we'll merge the replacements into the original track
    noteTracks = []
    for voice in voicesToReplace:
        noteTracks.append(getReplacementTrack(voice, preferredStyle, outOfStyleProb, ser))
    
    # actually merge tracks
    newTrack = tools.mergeMultipleTracks(trackWithMetaData=oldTrack, noteTracks=noteTracks)

    # Construct transformed midi file
    transformedMid = copy.deepcopy(mid)
    transformedMid.tracks[trackIndex] = newTrack
    
    return transformedMid

def getReplacementTrack(percVoice: str, preferredStyle: str, outOfStyleProb: int, ser: SeedExamplesRetriever) -> mido.MidiTrack:
    """
    Gets a replacement voice (midi track) using the seedExamplesRetriever.
    With a probability of (1-outOfStyleProb), the replacement voice will be from the given style.
    Note that we don't care if the replacement voice is empty or not.

    params
    percVoice: string denoting the voice to replace
    preferredStyle: style of the replacement voice
    outOfStyleProb: probability that the replacement voice will be from a different style
    ser: object to facilitate choosing replacement tracks
    """

    # ensure style is valid
    if preferredStyle not in ser.styles:
        raise Exception(f"Style {preferredStyle} not found in seedExamplesRetriever.")
    
    r = random.random()
    # determine if we will use an out of style replacement
    if r > outOfStyleProb:
        candidates = ser.getExamplesByStyle(preferredStyle)
    else:
        candidates = ser.getExamplesOutOfStyle(preferredStyle)

    assert len(candidates) > 0, f"No examples found for style {preferredStyle}"
    
    # choose a random example from the list of candidates
    replacementExample = random.choice(candidates)
    return replacementExample.getVoice(percVoice)

def getVoicesToReplace(fixedVoicesToReplace, numReplacements):
    return fixedVoicesToReplace if fixedVoicesToReplace != None else random.sample(PERC_VOICES, numReplacements) 

# def getVoicesToReplace(fixedVoicesToReplace, numReplacements: int, aer: AugExamplesRetriever) -> List[str]:
#     # TODO: test me
#     if fixedVoicesToReplace != None:
#         return fixedVoicesToReplace

#     voicesToReplace = []
    
#     for i in range(numReplacements):
#         voiceCounter = aer.getVoiceCounter()
#         eligibleVoices = [voice for voice in PERC_VOICES if voice not in voicesToReplace]
#         voices, probabilities = getVoiceDistributionFromCounter(voiceCounter, eligibleVoices)
#         voicesToReplace.append(np.random.choice(voices, p=probabilities))
#     return voicesToReplace

def getVoiceDistributionFromCounter(voiceCounter, eligibleVoices) -> (List[str], List[float]):
    """
    Given a counter object, returns a list of voices and a list of probabilities.
    Note that we only compute a distribution for the voices in the list "voices", even if other voices are present in the counter.
    """
    counts = [voiceCounter[voice] for voice in eligibleVoices]
    total = sum(counts)
    probabilities = [count/total for count in counts]
    return eligibleVoices, probabilities