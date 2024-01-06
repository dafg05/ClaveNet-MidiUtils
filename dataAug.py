from collections import Counter
from constants import *

import helpers
import mido
import os
import random


NUM_TRANSFORMATIONS = 7
REPLACEMENT_DIST = {
    "kick" : 0.6,
    "sna" : 0.5,
    "cym" : 1.0,
    "tom" : 0.6,
}

def augmentationScheme(sourceDir, outputDir, partsToProbablyReplace = None, numReplacements=1):
    """
    For every midi file in sourceDir, computes NUM_TRANSFORMATIONS transformed midi files
    and saves them in the outputDir. Note: we also write the unaltered file to the outputDir

    param
    sourceDir: dir that contains files to transform
    outputDir: dir that will contain transformations + unaltered files
    numReplacements: only needed if partsToProbablyReplace == None; aka 
    if we're going to randomly determine the partsToProbablyReplace for each transformation.
    If so, indicates the number of percussion parts that are going to be randomly replaced.
    partsToProbablyReplace: If specified, denotes the exact percussion parts that might be
    replaced per transformation. Randomly computed otherwise.

    We say partsToProbablyReplace because for each part, we denote a probability of replacement
    with the REPLACEMENT_DIST. Ex: if partsToProbablyReplace = ["kick", "cym"], there's still a chance that
    we don't actually replace "kick" but we do replace "cym"
    """

    fixedPartsToProbablyReplace = partsToProbablyReplace != None
    print(fixedPartsToProbablyReplace)
    for f in os.listdir(sourceDir):
        # Skip non-midi files
        if ".mid" not in f:
            continue
        mid = mido.MidiFile(f'{sourceDir}/{f}')
        mid.save(f"{outputDir}/{f}_original.mid")
        for i in range(NUM_TRANSFORMATIONS):
            if not fixedPartsToProbablyReplace:
                partsToProbablyReplace = random.sample(PERC_PARTS, numReplacements)
            
            partsToReplace = []
            for part in partsToProbablyReplace:
                willReplace = random.random() <= REPLACEMENT_DIST[part]
                if willReplace:
                    partsToReplace.append(part)
            
            newMid = transformMidiFile(mid, partsToReplace)
            newMid.save(f"{outputDir}/{f}_transformed_{i:03d}.mid")

def transformMidiFile(mid: mido.MidiFile, partsToReplace: list) -> mido.MidiFile:
    """
    Transforms a midi file by replacing parts with random examples

    params
    mid: Original midifile
    partsToReplace: strings denoting the parts that should be replaced

    returns
    transformedMid: transformed midiFile
    """
    track = mid.tracks[0]

    # delete parts from original track
    pitchesToDelete = []
    for p in partsToReplace:
        pitchesToDelete.extend(getPitches(p))
    track = helpers.deletePitches(track, pitchesToDelete)

    # determine tracksToMerge
    tracksToMerge = [track]
    for p in partsToReplace:
        tracksToMerge.append(getRandomReplacementTrack(p, EXAMPLES_DIR))
    
    # actually merge tracks
    newTrack = helpers.mergehelpersltipleTracks(tracksToMerge)
    
    # Construct transformed midi file
    transformedMid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
    transformedMid.tracks.append(newTrack)
    return transformedMid
    
def getRandomReplacementTrack(percPart: str, replacementDir: str) -> mido.MidiTrack:
    """
    Gets a random replacement track for the specified percPart from replacementDir
    """
    files = [f for f in os.listdir(replacementDir) if (".mid" in f) and (f.split("_")[0] == percPart)]
    if files == []:
        raise Exception(f'No replacement tracks of part {percPart} found at directory {replacementDir}')
    randomIndex = random.randint(0, len(files)-1)
    mid = mido.MidiFile(f"{replacementDir}/{files[randomIndex]}")
    # print(f"Picked {files[randomIndex]} as replacement for percPart {percPart}")
    return mid.tracks[0]

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

def concatenateMidiFiles(sourceDir: str, outputDir: str):
    """
    Concatenates all midi files in midiDir into a single midi file
    """
    files = [f for f in os.listdir(sourceDir) if ".mid" in f]
    firstMid = mido.MidiFile(f"{sourceDir}/{files[0]}")
    concatTrack = helpers.getBeginningMetaData(firstMid.tracks[0])
    for f in files:
        mid = mido.MidiFile(f"{sourceDir}/{f}")
        concatTrack = helpers.concatenateTracks(concatTrack, mid.tracks[0])
    concatTrack.append(mido.MetaMessage('end_of_track'))
    
    newMid = mido.MidiFile(ticks_per_beat=firstMid.ticks_per_beat)
    newMid.tracks.append(concatTrack)
    newMid.save(f"{outputDir}/concatenated.mid")

def getNumExamplesPerPercPart(dir) -> dict:
    d = Counter()
    for f in os.listdir(dir):
        percPart = f.split("_")[0]
        if percPart in PERC_PARTS:
            d[percPart] += 1
    return dict(d)

if __name__ == '__main__':
    augmentationScheme(DATA_AUG_SOURCE_DIR, DATA_AUG_OUTPUT_DIR, numReplacements=2)
    concatenateMidiFiles(DATA_AUG_OUTPUT_DIR, DATA_AUG_OUTPUT_DIR)