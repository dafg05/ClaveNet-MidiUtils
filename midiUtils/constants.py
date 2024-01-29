MIDI_DIR = "midi"
DATA_AUG_SOURCE_DIR = MIDI_DIR + "/augSource"
DATA_AUG_OUTPUT_DIR = MIDI_DIR + "/augOutput"
TEST_SOURCE_DIR  = MIDI_DIR + "/test"
TEST_OUTPUT_DIR = TEST_SOURCE_DIR + "/out"
WHOLE_DIR = MIDI_DIR + "/whole"
SPLIT_DIR = MIDI_DIR + "/split"
SEPARATE_DIR = MIDI_DIR + "/separate"
EXAMPLES_DIR = MIDI_DIR + "/examples"

SNA_DIR = EXAMPLES_DIR + "/sna"
KICK_DIR = EXAMPLES_DIR + "/kick"
CYM_DIR = EXAMPLES_DIR + "/cym"
TOM_DIR = EXAMPLES_DIR + "/tom"

END_OF_TRACK = "end_of_track"
NOTE_ON = 'note_on'
NOTE_OFF = 'note_off'

KICK_NOTES = [35,36]
SNA_NOTES = [32,34,37,38,39,40]
CYM_NOTES = [33,31,42,44,46,51,52,53,56,57,59]
TOM_NOTES = [41,43,45,47,48,50]

PERC_PARTS = ["kick", "sna", "cym", "tom"]

TEST_MIDI_FILE = TEST_SOURCE_DIR + "/1_rock_110_beat_4-4_slice_208.mid"
TEST_EXCLUDE_OUT = TEST_OUTPUT_DIR + "/exclude_pitches.mid"
TEST_INCLUDE_OUT = TEST_OUTPUT_DIR + "/include_pitches.mid"
TEST_PITCHES = [36,44] # kick and hihat foot close
TEST_MERGEE_1 = TEST_SOURCE_DIR + "/mergee1.mid"
TEST_MERGEE_2 = TEST_SOURCE_DIR + "/mergee2.mid"
TEST_MERGEE_3 = TEST_SOURCE_DIR + "/mergee3.mid"
TEST_SIMPLE_MERGED_OUT = TEST_OUTPUT_DIR + "/merged_simple.mid"
TEST_MULTIPLE_MERGED_OUT = TEST_OUTPUT_DIR + "/merged_multiple.mid"

