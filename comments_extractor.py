from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime

from bs4 import BeautifulSoup

import argparse
import logging
import re
import unicodedata
import pandas as pd


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
COLUMNS = ["ID", "COMMENT_TEXT", "SPAN_TEXT", "FILENAME"]

logger = logging.getLogger("comments_extractor")


def configure_logging(log_dir=None, console=True):
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        progress_handler = logging.FileHandler(log_dir / "progress.log", mode="a", encoding="utf-8")
        progress_handler.setLevel(logging.INFO)
        progress_handler.setFormatter(formatter)
        logger.addHandler(progress_handler)

        error_handler = logging.FileHandler(log_dir / "errors.log", mode="a", encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console_handler)

    logger.info(f"=== Run started {datetime.now().isoformat(timespec='seconds')} ===")

    return log_dir


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
    errors = []

    total = len(files)

    for index, file in enumerate(files, start=1):
        if show_progress:
            logger.info(f"[{index}/{total}] Extracting comments from {file.name}")

        try:
            records = extract_comment_data(file)
        except Exception as error:
            message = str(error)
            logger.error(f"Failed to extract comments from {file.name}: {message}")
            errors.append((file, message))
            records = []

        records_by_file[file] = records
        all_records.extend(records)

    return all_records, records_by_file, errors


def write_csv(records, path):
    df = pd.DataFrame.from_records(data=records, columns=COLUMNS)
    df.to_csv(path, index=False)


def save_combined_csv(files, save_path):
    all_records, _, errors = extract_files(files)
    write_csv(all_records, save_path)
    logger.info(f"Saved combined CSV with {len(all_records)} comment(s) to {save_path}")
    return errors


def resolve_separate_csv_paths(files):
    proposed = {file: file.with_suffix(".csv") for file in files}

    counts = {}
    for path in proposed.values():
        counts[path] = counts.get(path, 0) + 1

    colliding_paths = {path for path, count in counts.items() if count > 1}

    paths = {}
    warnings = []

    for file, path in proposed.items():
        if path in colliding_paths:
            fallback = file.with_name(f"{file.name}.csv")
            paths[file] = fallback
            warnings.append(
                f"'{path.name}' would be used by more than one file; "
                f"saving {file.name} as {fallback.name} instead."
            )
        else:
            paths[file] = path

    return paths, warnings


def save_separate_csvs(files):
    _, records_by_file, errors = extract_files(files)

    paths, warnings = resolve_separate_csv_paths(files)

    for warning in warnings:
        logger.warning(warning)

    for file, records in records_by_file.items():
        write_csv(records, paths[file])
        logger.info(f"Saved {len(records)} comment(s) from {file.name} to {paths[file].name}")

    return errors

def default_output_path(path):
    if path.is_file():
        return path.with_suffix(".csv")

    if path.is_dir():
        return path / f"{path.name}.csv"

    return Path.cwd() / "comments.csv"

def main(args):
    log_dir = configure_logging(args.log_dir, console=not args.quiet)

    if log_dir:
        logger.info(f"Logs for this run: {log_dir / 'progress.log'} and {log_dir / 'errors.log'}")

    files = get_files(args.data)
    logger.info(f"Found {len(files)} file(s) to process in {args.data}")

    if args.separate:
        errors = save_separate_csvs(files)
    else:
        if args.save:
            save_path = args.save
        elif args.data.is_file():
            save_path = args.data.with_suffix(".csv")
        else:
            save_path = args.data / f"{args.data.name}.csv"

        errors = save_combined_csv(files, save_path)

    if errors:
        if log_dir:
            logger.info(f"{len(errors)} of {len(files)} file(s) failed -- see errors.log for details.")
        else:
            logger.info(f"{len(errors)} of {len(files)} file(s) failed:")
            for file, message in errors:
                logger.info(f"  - {file.name}: {message}")

    logger.info("=== Run finished ===")


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

    parser.add_argument(
        "--log-dir",
        type=Path,
        required=False,
        default=None,
        help="Write progress.log and errors.log to this directory. If omitted, nothing is written to disk.",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress terminal output. Has no effect on --log-dir; if that's set, the log files are still written.",
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