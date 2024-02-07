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
        self.voices = self.__getVoices()
        self.filename = self.__getFilename(midi_path)

    def __getFilename(self, midi_path):
        return os.path.basename(midi_path)
    
    def __getVoices(self):

        voices = []
        for v in PERC_VOICES_MAPPING.keys():
            if self.hasVoice(v):
                voices.append(v)
        return voices

    def __getVoiceTrack(self, voice) -> mido.MidiTrack():
        """
        Returns a midi track that contains only the specified voice
        """
        pitches = PERC_VOICES_MAPPING[voice]
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
        
        # examples by style dict
        self._examplesByStyle = {style: [] for style in self.styles}
        for f in os.listdir(dir):
            if f.endswith(".mid"):
                style = f.split("_")[0]
                augExample = AugSeedExample(midi_path=f"{dir}/{f}", style=style)
                self._examplesByStyle[style].append(augExample)     

    def getExamplesByStyle(self, style) -> List[AugSeedExample]:
        """
        Returns a list of AugSeedExamples given a style
        """
        if style not in self.styles:
            return []
        return self._examplesByStyle[style]
    
    def getExamplesOutOfStyle(self, style) -> List[AugSeedExample]:
        """
        Returns a list of AugSeedExamples that are not of the specified style
        """
        outOfStyleExamples = []
        for s in self.styles:
            if s != style:
                outOfStyleExamples.extend(self._examplesByStyle[s])
        return outOfStyleExamples
    
    def getCandidateTracksInfo(self, preferredStyle: str, outOfStyle: bool, voicesToExclude):
        """
        Returns a list of tuples (filename, voice) for candidate tracks to use in data augmentation.
        If outOfStyle is True, the returned tracks will NOT be of the preferred style.
        Any tracks whose voice is in voicesToExclude will be removed from the list.
        """

        examples = self.getExamplesOutOfStyle(preferredStyle) if outOfStyle else self.getExamplesByStyle(preferredStyle)
        trackInfo = []
        for ae in examples:
            for v in ae.voices:
                trackInfo.append((ae.filename, v))
        
        # remove tracks from voices to exclude
        trimmedTrackInfo = []
        for ti in trackInfo:
            if not ti[1] in voicesToExclude:
                trimmedTrackInfo.append(ti)
        return trimmedTrackInfo
    
    def getTrack(self, filename, voice):
        """
        Assumes that the filename in the examplesByStyle dict is unique,
        which it should be since every example is a different file in the same directory.
        Returns a midi track containing only the specified voice.
        """
        for style in self.styles:
            for ae in self.getExamplesByStyle(style):
                if ae.filename == filename:
                    return ae.getVoice(voice)
        return mido.MidiTrack()

    def __str__(self) -> str:
        return f'SeedExamplesRetriever with styles {self.styles}, at dir "{self.dir}"'