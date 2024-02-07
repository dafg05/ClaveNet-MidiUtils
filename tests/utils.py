import os
import shutil
import midiUtils.synth as synth

def clearOutputDir(outputDir):
    for f in os.listdir(outputDir):
        if not os.path.isdir(f"{outputDir}/{f}"):
            os.remove(f"{outputDir}/{f}")

    audioDir = f"{outputDir}/audio"
    if os.path.exists(audioDir):
        shutil.rmtree(audioDir)


def synthesizeOutputDir(outputDir):
    audioDir = f"{outputDir}/audio"
    if not os.path.exists(audioDir):
        os.makedirs(audioDir)
    synth.synthesize_all(outputDir, audioDir)