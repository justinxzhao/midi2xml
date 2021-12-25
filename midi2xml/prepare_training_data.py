"""Script to convert Performances and musicXML to TSV for training."""

import csv
import json
import os
import random
from typing import Sequence

from absl import app
from absl import flags
import xmltodict

from midi2xml.constants import PERFORMANCE_ENCODING

flags.DEFINE_string("performances_dir", None, "Directory of performance files.")
flags.DEFINE_string("xml_dir", None, "Directory of musicXML files.")
flags.DEFINE_string("output_dir", None, "Output directory.")

FLAGS = flags.FLAGS


def encode_performance(performance):
    tokenized_performance = performance.split("\n")
    tokens = []
    for token in tokenized_performance:
        if token:
            tokens.append(PERFORMANCE_ENCODING[token])
    return " ".join(tokens)


def sanitize_json(json_object):
    """Removes lyrics, default-x, default-y."""
    if isinstance(json_object, dict):
        if "lyric" in json_object:
            del json_object["lyric"]
        if "@default-x" in json_object:
            del json_object["@default-x"]
        if "@default-y" in json_object:
            del json_object["@default-y"]
        if "part-abbreviation" in json_object:
            del json_object["part-abbreviation"]
        if "work" in json_object:
            del json_object["work"]
        if "encoding" in json_object:
            del json_object["encoding"]
        if "@version" in json_object:
            del json_object["@version"]
        if "identification" in json_object:
            del json_object["identification"]
        if "movement-title" in json_object:
            del json_object["movement-title"]
        if "defaults" in json_object:
            del json_object["defaults"]
        if "@color" in json_object:
            del json_object["@color"]
        if "@font-style" in json_object:
            del json_object["@font-style"]
        if "@font-weight" in json_object:
            del json_object["@font-weight"]
        if "@font-family" in json_object:
            del json_object["@font-family"]
        if "system-layout" in json_object:
            del json_object["system-layout"]
        if "@id" in json_object:
            del json_object["@id"]
        if "@parentheses" in json_object:
            del json_object["@parentheses"]
        if "@words" in json_object:
            del json_object["@words"]
        if "words" in json_object:
            del json_object["words"]
        if "#text" in json_object:
            del json_object["#text"]
        if "print" in json_object:
            del json_object["print"]
        if "notehead" in json_object:
            del json_object["notehead"]
        for key, subobject in json_object.items():
            json_object[key] = sanitize_json(subobject)

    if isinstance(json_object, list):
        for index, subobject in enumerate(json_object):
            json_object[index] = sanitize_json(subobject)
    return json_object


def simplify_xml(xml_file):
    """Returns simplified representation of music XML."""
    # Convert the whole thing to a JSON string, remove irrelevant attributes, and
    # then flatten.
    data_dict = xmltodict.parse(xml_file.read())
    json_data = json.dumps(data_dict)
    json_object = json.JSONDecoder().decode(json_data)
    json_object = sanitize_json(json_object)
    json_str = str(json_object)

    # Encode keywords.
    # for index, keyword in enumerate(KEYWORDS):
    #   json_str = json_str.replace(keyword, str(index))

    # Flatten.
    return (
        " ".join(json_str.replace("\n", " ").replace("\t", " ").split())
        .replace('"', "")
        .replace("'", "")
    )


def main(argv: Sequence[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")

    os.makedirs(FLAGS.output_dir)

    piece_ids = os.listdir(FLAGS.performance_dir)
    test_piece_ids = random.choices(piece_ids, k=10)
    training_piece_ids = [
        piece_id for piece_id in piece_ids if piece_id not in test_piece_ids
    ]

    with open(
        os.path.join(FLAGS.output_dir, "train_pieces.txt"), "w"
    ) as train_pieces_file:
        train_pieces_file.write("\n".join(training_piece_ids))

    with open(
        os.path.join(FLAGS.output_dir, "test_pieces.txt"), "w"
    ) as test_pieces_file:
        test_pieces_file.write("\n".join(test_piece_ids))

    # Also writes input and output to train word piece models.
    with open(os.path.join(FLAGS.output_dir, "music21.train.tsv"), "w") as train_tsv:
        with open(os.path.join(FLAGS.output_dir, "music21.test.tsv"), "w") as test_tsv:
            with open(
                os.path.join(FLAGS.output_dir, "music21.train.input"), "w"
            ) as train_input:
                with open(
                    os.path.join(FLAGS.output_dir, "music21.train.output"), "w"
                ) as train_output:
                    train_writer = csv.writer(train_tsv, delimiter="\t")
                    test_writer = csv.writer(test_tsv, delimiter="\t")
                    for piece_id in piece_ids:
                        print("Processing ID: " + piece_id)
                        # XML paths come from music21 script.
                        # Performance paths come from running magenta script.
                        performance_path = os.path.join(
                            FLAGS.performances_dir + piece_id
                        )
                        xml_path = os.path.join(
                            FLAGS.xml_dir, piece_id.strip(".midi.txt") + ".xml"
                        )
                        if not os.path.exists(performance_path) or not os.path.exists(
                            xml_path
                        ):
                            print(
                                f"Either performance path: {performance_path} or xml path: {xml_path} doesn't exist."
                            )
                            continue

                        with open(performance_path) as performance_file:
                            performance_content = encode_performance(
                                performance_file.read()
                            )
                        with open(xml_path) as xml_file:
                            xml_content = simplify_xml(xml_file)

                        if piece_id in test_piece_ids:
                            test_writer.writerow([performance_content, xml_content])
                        else:
                            train_writer.writerow([performance_content, xml_content])
                            train_input.write(performance_content + "\n")
                            train_output.write(xml_content + "\n")


if __name__ == "__main__":
    app.run(main)
