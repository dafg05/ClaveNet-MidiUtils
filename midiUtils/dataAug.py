from midiUtils.constants import *
from midiUtils import helpers
from midiUtils.augExamples import AugExamplesRetriever, AugExample

import mido
import os
import random
import copy

def augmentationScheme(sourceDir, outputDir, examplesDir, styleParams, numTransformations = 3, fixedPartsToReplace = None, numReplacements=1, seed=0, debug=False):
    """
    For every midi file in sourceDir, computes NUM_TRANSFORMATIONS transformed midi files
    and saves them in the outputDir. 
    Note: we also write the original file to the outputDir

    param
    sourceDir: dir that contains files to transform
    outputDir: dir that will contain transformations + unaltered files
    numTransformations: number of transformations to compute for each midi file, not including the original
    fixedPartsToReplace: If specified, denotes the exact percussion parts that will be replaced. Else,
    parts to replace will be randomly computed.
    numReplacements: If fixedPartsToReplace is not specified, then this denotes the number of 
    randomly chosen parts to replace. Else, this parameter is ignored.
    styleParams: keys are "preferredStyle" and "outOfStyleProb". 

    """

    random.seed(seed)

    augExamplesRetriever = AugExamplesRetriever(dir=examplesDir)
    for f in os.listdir(sourceDir):
        # Skip non-midi files
        if ".mid" not in f:
            continue
        mid = mido.MidiFile(f'{sourceDir}/{f}')
        mid.save(f"{outputDir}/{f}_original.mid")
        for i in range(numTransformations):
            partsToReplace = getPartsToReplace(fixedPartsToReplace, numReplacements)
            trackIndex = 0

            newMid = transformMidiFile(mid, trackIndex, partsToReplace, augExamplesRetriever, styleParams, debug)
            newMid.save(f"{outputDir}/{f}_tra-{i:02d}.mid")

def transformMidiFile(mid: mido.MidiFile, trackIndex: int, partsToReplace: list, augExamplesRetriever: AugExamplesRetriever, styleParams: dict, debug=False) -> mido.MidiFile:
    """
    Transforms a midi file by probably replacing the specified parts with parts from the same style;
    otherwise replaces with parts from a different style.

    params
    mid: Original midifile
    trackIndex: the miditrack the replacement algorithm will be run
    partsToReplace: strings denoting the parts that should be replaced
    augExamplesRetriever: object to facilitate choosing replacement tracks
    styleParams: keys are "preferredStyle" and "outOfStyleProb". 

    returns
    transformedMid: transformed midiFile, which is a copy of the original save for the new track.
    """
    if debug:
        print(f"Transforming midi file {mid.filename} with parts: {partsToReplace}, trackIndex: {trackIndex}, preferredStyle: {styleParams['preferredStyle']}, outOfStyleProb: {styleParams['outOfStyleProb']}")

    oldTrack = mid.tracks[trackIndex]
    preferredStyle = styleParams["preferredStyle"]
    outOfStyleProb = styleParams["outOfStyleProb"]

    if preferredStyle == "":
        preferredStyle = random.choice(augExamplesRetriever.styles)

    # delete parts to replace from original track
    pitchesToDelete = []
    for p in partsToReplace:
        pitchesToDelete.extend(helpers.getPitches(p))
    oldTrack = helpers.deletePitches(oldTrack, pitchesToDelete)

    # determine tracksToMerge
    tracksToMerge = [oldTrack]
    for p in partsToReplace:
        tracksToMerge.append(getReplacementTrack(p, preferredStyle, outOfStyleProb, augExamplesRetriever))
    
    try:
        # actually merge tracks
        newTrack = helpers.mergeMultipleTracks(tracksToMerge)
    except Exception as e:
        raise Exception(f"Something went wrong when trying to merge tracks. oldTrack: {oldTrack}, len(tracksToMerge): {len(tracksToMerge)}")

    # Construct transformed midi file
    transformedMid = copy.deepcopy(mid)
    transformedMid.tracks[trackIndex] = newTrack
    
    return transformedMid

def getReplacementTrack(percPart: str, preferredStyle: str, outOfStyleProb: int, augExamplesRetriever: AugExamplesRetriever) -> mido.MidiTrack:
    """
    Gets a replacement part (midi track) using the augExamplesRetriever.
    With a probability of (1-outOfStyleProb), the replacement part will be from the given style.
    Note that we don't care if the replacement part is empty or not.

    params
    percPart: string denoting the part to replace
    preferredStyle: style of the replacement part
    outOfStyleProb: probability that the replacement part will be from a different style
    augExamplesRetriever: object to facilitate choosing replacement tracks
    """

    # ensure style is valid
    if preferredStyle not in augExamplesRetriever.styles:
        raise Exception(f"Style {preferredStyle} not found in augExamplesRetriever")
    
    r = random.random()
    # determine if we will use an out of style replacement
    if r > outOfStyleProb:
        candidates = augExamplesRetriever.getExamplesByStyle(preferredStyle)
    else:
        candidates = augExamplesRetriever.getExamplesOutOfStyle(preferredStyle)

    assert len(candidates) > 0, f"No examples found for style {preferredStyle}"
    
    # choose a random example from the list of candidates
    replacementExample = random.choice(candidates)
    return replacementExample.getPart(percPart)

def getPartsToReplace(fixedPartsToReplace, numReplacements):
    return fixedPartsToReplace if fixedPartsToReplace != None else random.sample(PERC_PARTS, numReplacements)