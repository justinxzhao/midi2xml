"""Parses pieces from the music21 corpus to generate midi / musicXML training examples."""

import music21
import os

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string("output_dir", None, "Directory to write output files.")
flags.DEFINE_integer(
    "fragment_measure_length", 2, "Number of measures to use for each example."
)


def piece_to_midi_to_xml_bytes(piece):
    mf = music21.midi.translate.streamToMidiFile(piece)
    stream = music21.midi.translate.midiFileToStream(mf)
    GEX = music21.musicxml.m21ToXml.GeneralObjectExporter(stream)
    out = GEX.parse()
    return out


def get_num_measures(piece):
    return len(piece.parts[0].measures(0, None))


def split_into_subpieces(piece):
    subpieces = []
    num_measures = get_num_measures(piece)
    for i in range(num_measures - FLAGS.fragment_measure_length + 1):
        start_measure = i
        end_measure = i + FLAGS.fragment_measure_length
        # Consider expanding this to more parts.
        xml_target = piece.parts[0].measures(start_measure, end_measure)
        midi_source = piece.measures(start_measure, end_measure)
        subpieces.append((midi_source, xml_target))
    return subpieces


def main() -> None:
    # paths = music21.corpus.getPaths('musicxml')
    paths = music21.corpus.search("bach", fileExtensions="xml")
    for i, path in enumerate(paths):
        print("processing piece #: " + str(i) + " / " + str(len(paths)))
        print("processing piece: " + str(path))

        try:
            piece = path.parse()
            subpieces = split_into_subpieces(piece)
            for j, subpiece in enumerate(subpieces):
                subpiece[0].write(
                    "midi",
                    os.path.join(
                        FLAGS.output_dir,
                        "pieces",
                        str(i) + "." + str(j) + ".midi",
                    ),
                )
                subpiece[1].write(
                    "musicxml",
                    os.path.join(
                        FLAGS.output_dir,
                        str(i) + "." + str(j) + ".musicxml",
                    ),
                )

        except Exception as e:
            print("ERROR with processing. Skipping: ", e)


if __name__ == "__main__":
    app.run(main)
