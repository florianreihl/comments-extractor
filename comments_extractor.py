from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from tqdm import tqdm

import argparse
import re
import unicodedata
import pandas as pd


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
COLUMNS = ["ID", "COMMENT_TEXT", "SPAN_TEXT", "FILENAME"]


def norm(text):
    return unicodedata.normalize("NFKD", text or "").strip()


def get_xml_text(element):
    return norm("".join(t.text or "" for t in element.findall(".//w:t", NS)))


def extract_word_comments(file):
    with ZipFile(file) as docx:
        try:
            comments_xml = docx.read("word/comments.xml")
            document_xml = docx.read("word/document.xml")
        except KeyError:
            return []

    comments_root = ET.fromstring(comments_xml)
    document_root = ET.fromstring(document_xml)

    comments = {}

    for comment in comments_root.findall(".//w:comment", NS):
        comment_id = comment.attrib[f"{{{NS['w']}}}id"]
        comments[comment_id] = get_xml_text(comment)

    spans = {}

    for start in document_root.findall(".//w:commentRangeStart", NS):
        comment_id = start.attrib[f"{{{NS['w']}}}id"]

        parent = None
        for elem in document_root.iter():
            if start in list(elem):
                parent = elem
                break

        if parent is None:
            spans[comment_id] = ""
            continue

        children = list(parent)
        start_index = children.index(start)

        collected = []
        inside = False

        for child in children[start_index:]:
            if child.tag.endswith("commentRangeStart"):
                inside = True
                continue

            if child.tag.endswith("commentRangeEnd"):
                break

            if inside:
                collected.append(get_xml_text(child))

        spans[comment_id] = norm("".join(collected))

    return [
        (comment_id, comment_text, spans.get(comment_id, ""), file.name)
        for comment_id, comment_text in comments.items()
    ]


def extract_google_doc_comments(file):
    with open(file, "r", encoding="utf-8") as src:
        soup = BeautifulSoup(src, features="html.parser")

    comments_pattern = re.compile(r"cmnt\d+")
    comments = [element.parent for element in soup.find_all(id=comments_pattern)]

    def get_prev_span(element):
        while element and element.name != "span":
            element = element.previous_sibling
        return element

    data = []

    for comment in comments:
        comment_id = norm(comment.a["id"])
        comment_text = norm(comment.span.text)

        linked_spans = []

        for element in soup.find_all(id=comment.a["href"][1:]):
            prev_span = get_prev_span(element.parent)
            if prev_span:
                linked_spans.append(norm(prev_span.text))

        if len(linked_spans) != 1:
            raise ValueError(
                f"Comment {comment_id} in {file.name} corresponds to 0 or more than 1 text span"
            )

        data.append((comment_id, comment_text, linked_spans[0], file.name))

    return data


def extract_comment_data(file):
    extension = file.suffix.lower()

    if extension == ".docx":
        return extract_word_comments(file)

    if extension in [".html", ".htm"]:
        return extract_google_doc_comments(file)

    return []


def get_files(path):
    if path.is_file():
        return [path]

    if path.is_dir():
        files = []
        files.extend(path.glob("*.docx"))
        files.extend(path.glob("*.html"))
        files.extend(path.glob("*.htm"))
        return files

    raise ValueError(f"{path} does not exist.")

def extract_files(files, show_progress=True):
    all_records = []
    records_by_file = {}

    iterator = tqdm(files, desc="Extracting Comments") if show_progress else files

    for file in iterator:
        records = extract_comment_data(file)
        records_by_file[file] = records
        all_records.extend(records)

    return all_records, records_by_file


def write_csv(records, path):
    """Write a list of comment records to a CSV file at `path`.

    Shared by the CLI and the GUI so both save data the same way.
    """
    df = pd.DataFrame.from_records(data=records, columns=COLUMNS)
    df.to_csv(path, index=False)


def save_combined_csv(files, save_path):
    all_records, _ = extract_files(files)
    write_csv(all_records, save_path)


def save_separate_csvs(files):
    _, records_by_file = extract_files(files)

    for file, records in records_by_file.items():
        write_csv(records, file.with_suffix(".csv"))

def default_output_path(path):
    if path.is_file():
        return path.with_suffix(".csv")

    if path.is_dir():
        return path / f"{path.name}.csv"

    return Path.cwd() / "comments.csv"

def main(args):
    files = get_files(args.data)

    if args.separate:
        save_separate_csvs(files)
        return

    if args.save:
        save_path = args.save
    elif args.data.is_file():
        save_path = args.data.with_suffix(".csv")
    else:
        save_path = args.data / f"{args.data.name}.csv"

    save_combined_csv(files, save_path)


def add_args(parser):
    parser.add_argument(
        "-d",
        "--data",
        type=Path,
        required=True,
        help="A .docx/.html file or a folder containing .docx/.html files.",
    )

    parser.add_argument(
        "-s",
        "--save",
        type=str,
        required=False,
        help="The save path for the combined CSV file.",
    )

    parser.add_argument(
        "--separate",
        action="store_true",
        help="Create one CSV file per document.",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        formatter_class=argparse.RawTextHelpFormatter,
        description="Extract comments from Microsoft Word .docx files and Google Docs HTML exports.",
    )

    add_args(parser)
    args = parser.parse_args()
    main(args)