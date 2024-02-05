import os
import mido

from midiUtils.constants import *
from midiUtils import tools

from typing import List
from collections import Counter

class AugSeedExample:
    def __init__(self, midi_path, style):
        self.midi_path = midi_path
        self.style = style

    def __getVoiceTrack(self, voice) -> mido.MidiTrack():
        """
        Returns a midi track that contains only the specified voice
        """
        pitches = tools.getPitches(voice)
        mid = mido.MidiFile(self.midi_path)
        track = mid.tracks[0]
    
        return tools.getTrackWithSelectPitches(track, pitches, notesOnly=True)

    def getVoice(self, voice) -> mido.MidiTrack():
        """
        Returns a midi track that contains only the specified voice
        """
        if not self.hasVoice(voice):
            return mido.MidiTrack()
        return self.__getVoiceTrack(voice)
    
    def hasVoice(self, voice) -> bool:
        """
        Returns true if the example has the specified voice
        """
        track = self.__getVoiceTrack(voice)
        return not tools.isTrackEmpty(track)

    def __str__(self) -> str:
        return f'AugExample of style "{self.style}" at midi_path: "{self.midi_path}"'

class SeedExamplesRetriever:
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
            raise Exception(f"Must have at least 2 styles in {dir} to construct SeedExamplesRetriever.")
        
        # examplesDict
        self.examplesDict = {style: [] for style in self.styles}
        for f in os.listdir(dir):
            if f.endswith(".mid"):
                style = f.split("_")[0]
                augExample = AugSeedExample(midi_path=f"{dir}/{f}", style=style)
                self.examplesDict[style].append(augExample)         

    def getExamplesByStyle(self, style) -> List[AugSeedExample]:
        """
        Returns a list of AugSeedExamples given a style
        """
        if style not in self.styles:
            return []
        return self.examplesDict[style]
    
    def getExamplesOutOfStyle(self, style) -> List[AugSeedExample]:
        """
        Returns a list of AugSeedExamples that are not of the specified style
        """
        outOfStyleExamples = []
        for s in self.styles:
            if s != style:
                outOfStyleExamples.extend(self.examplesDict[s])
        return outOfStyleExamples
    
    def getVoiceCounts(self) -> Counter:
        # TODO: implement this
        raise NotImplementedError
    
    def __str__(self) -> str:
        return f'SeedExamplesRetriever with styles {self.styles}, at dir "{self.dir}"'