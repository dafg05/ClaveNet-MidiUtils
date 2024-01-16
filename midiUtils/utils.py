from midiUtils.constants import *
from midiUtils import helpers

import mido
import os
from pathlib import Path


def splitMidiFileByBarSteps(sourcePath, split_dir, barStep: int = 1):
    """
    Assumes single midi track per file
    """

    beatsPerBar = 4 # hard code 4/4 time signature
    
    mid = mido.MidiFile(sourcePath)
    track = mid.tracks[0]

    bars = helpers.splitMidiTrackIntoBars(track, barStep, beatsPerBar, mid.ticks_per_beat)

    fileSplitDir = split_dir
    Path(fileSplitDir).mkdir(parents=True, exist_ok=True)

    fileName = sourcePath.split("/")[-1] # get filename from path
    fileName = fileName.split(".")[0] # remove extension

    for i in range(len(bars)):
        b = bars[i]
        newMid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
        newMid.tracks.append(b)
        newMid.save(f"{fileSplitDir}/{fileName}_slice_{i:03d}.mid")

def separateMidiFileByPitches(sourcePath, separationName, pitches):
    """
    Assumes single midi track per file
    """

    mid = mido.MidiFile(sourcePath)
    track = mid.tracks[0]

    newTrack = helpers.getTrackWithSelectPitches(track, pitches)

    fileName = sourcePath.split("/")[-1] # get filename from path
    fileName = fileName.split(".")[0] # remove extension

    newMid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
    newMid.tracks.append(newTrack)
    newMid.save(f"{SEPARATE_DIR}/{fileName}_{separationName}.mid")

def trimMidiFile(sourcePath, outPath, startBar:int=0, endBar:int=2, beatsPerBar: int=4):
    """
    Assumes single midi track per file
    """
    mid = mido.MidiFile(sourcePath)
    track = mid.tracks[0]
    
    newTrack = helpers.trimMidiTrack(track, startBar, endBar, beatsPerBar, mid.ticks_per_beat)
    
    mid.tracks = [newTrack]
    mid.save(outPath)


if __name__ == "__main__":
    print("hello world")
