import os
import mido

from midiUtils.constants import *
from midiUtils import helpers
from typing import List

class AugExample:
    def __init__(self, midi_path, style):
        self.midi_path = midi_path
        self.style = style

    def getPart(self, part) -> mido.MidiTrack():
        """
        Returns a midi track that contains only the specified part
        """
        pitches = helpers.getPitches(part)
        mid = mido.MidiFile(self.midi_path)
        track = mid.tracks[0]
    
        return helpers.getTrackWithSelectPitches(track, pitches)
    
    def hasPart(self, part) -> bool:
        """
        Returns true if the example has the specified part
        """
        track = self.getPart(part)
        return not helpers.isTrackEmpty(track)

    def __str__(self) -> str:
        return f'AugExample of style "{self.style}" at midi_path: "{self.midi_path}"'

class AugExamplesRetriever:
    def __init__(self, dir):
        # dir
        self.dir = dir
        # styles
        styleSet = set()
        for f in os.listdir(dir):
            if f.endswith(".mid"):
                style = f.split("_")[0]
                styleSet.add(style)
        self.styles = list(styleSet)
        if len(self.styles) < 2:
            raise Exception(f"Must have at least 2 styles in {dir} to construct AugExamplesRetriever.")
        
        # examplesDict
        self.examplesDict = {style: [] for style in self.styles}
        for f in os.listdir(dir):
            if f.endswith(".mid"):
                style = f.split("_")[0]
                augExample = AugExample(midi_path=f"{dir}/{f}", style=style)
                self.examplesDict[style].append(augExample)         

    def getExamplesByStyle(self, style) -> List[AugExample]:
        """
        Returns a list of AugExamples given a style
        """
        if style not in self.styles:
            return []
        return self.examplesDict[style]
    
    def getExamplesOutOfStyle(self, style) -> List[AugExample]:
        """
        Returns a list of AugExamples that are not of the specified style
        """
        outOfStyleExamples = []
        for s in self.styles:
            if s != style:
                outOfStyleExamples.extend(self.examplesDict[s])
        return outOfStyleExamples
    
    def __str__(self) -> str:
        return f'AugExamplesRetriever with styles {self.styles}, at dir "{self.dir}"'
    
if __name__ == "__main__":

    testDir = f"{EXAMPLES_DIR}/test"

    # retriever constructor test
    augExamplesRetriever = AugExamplesRetriever(testDir)
    print(f"constructing aer: {augExamplesRetriever}")

    # styles test
    print(f"styles test: {augExamplesRetriever.styles}")

    # getExamplesByStyle test
    l = augExamplesRetriever.getExamplesByStyle('mambo')
    print("getExamplesByStyle test (using mambo as style):")
    for e in l:
        print(e)

    # getExamplesOutOfStyle test
    l = augExamplesRetriever.getExamplesOutOfStyle('songo')
    print("getExamplesOutOfStyle test (using songo as style):")
    for e in l:
        print(e)

    # aug example constructor test
    augExample = augExamplesRetriever.getExamplesByStyle("songo")[0]
    print(f"now testing augExample: {augExample}")
    # midiPath test
    print(f"midiPath test: {augExample.midi_path}")
    # style test
    print(f"style test: {augExample.style}")
    # hasPart test
    print(f"does augExample have kick part? {augExample.hasPart('kick')}")
    print(f"does augExample have tom part? {augExample.hasPart('tom')}")
    # getPart test
    mid = mido.MidiFile()
    mid.tracks.append(augExample.getPart("kick"))
    mid.save(f"{testDir}/out/augExampleSongoKick.mid")
    print(f"saved augExampleSongoKick.mid")
    
    




