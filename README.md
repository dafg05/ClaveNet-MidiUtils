# MIDI UTILS

A variety of midi manipulation utilities for the drum generator.

## Data Augmentation

The main function in **dataAug.py** is `transformMidiFile`. Ultimately, this function randomly replaces some of the percussion voices of an input midi file with voices belonging to a randomly chosen "seedExample". Parameters of the function allow for more precise control on how many voices to swap out and whether we want the replacement voices to belong to the same style. 

An crucial parameter to this function is a `SeedExamplesRetriever`, the definition of which is found in **augExamples.py**. A folder of 2-bar midi drum 'seed examples' is needed to initialize an object of this type. Once initialized, a seedExamplesRetriever allows for in-style and out-of-style random sampling of the pool of voice tracks (which is extracted from the list of seed examples).

## Absolute Time Tracks

A class that's based on mido's `MidiTrack`, except that it stores absolute time alongside midi messages. Created to avoid having to deal with delta-time when manipulating midi.

## Midi Editing
Between **absTrack.py** and **tools.py** there are functions to:

* Trim a midi file
* Delete specific pitches from a track
* Merge multiple tracks
* Randomly offset time and velocities of tracks
* Get a track containly only note messages

## Synth

synth.py is a very light wrapper on the `pyfluidsynth` package to automate synthesizing midi directories.