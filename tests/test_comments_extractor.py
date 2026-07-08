import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from comments_extractor import main


class Args:
    def __init__(self, data, save=None, separate=False):
        self.data = Path(data)
        self.save = save
        self.separate = separate


def test_sample_file_extracts_comment(tmp_path):
    sample_file = Path(__file__).parent / "data" / "sample.docx"
    output_csv = tmp_path / "comments.csv"

    main(Args(sample_file, output_csv))

    assert output_csv.exists()

    df = pd.read_csv(output_csv)

    assert list(df.columns) == [
        "ID",
        "COMMENT_TEXT",
        "SPAN_TEXT",
        "FILENAME",
    ]

    assert len(df) == 1
    assert df.iloc[0]["COMMENT_TEXT"] == "This is a test comment."
    assert df.iloc[0]["SPAN_TEXT"] == "sample document"
    assert df.iloc[0]["FILENAME"] == "sample.docx"


def test_separate_csv_output(tmp_path):
    sample_file = Path(__file__).parent / "data" / "sample.docx"

    # Copy sample into a temporary directory so we don't write into tests/data
    copied_sample = tmp_path / "sample.docx"
    copied_sample.write_bytes(sample_file.read_bytes())

    main(Args(copied_sample, separate=True))

    output_csv = tmp_path / "sample.csv"

    assert output_csv.exists()

    df = pd.read_csv(output_csv)

    assert list(df.columns) == [
        "ID",
        "COMMENT_TEXT",
        "SPAN_TEXT",
        "FILENAME",
    ]

    assert len(df) == 1
    assert df.iloc[0]["COMMENT_TEXT"] == "This is a test comment."
    assert df.iloc[0]["SPAN_TEXT"] == "sample document"
    assert df.iloc[0]["FILENAME"] == "sample.docx"

def test_default_output_filename(tmp_path):
    sample_file = Path(__file__).parent / "data" / "sample.docx"

    copied_sample = tmp_path / "sample.docx"
    copied_sample.write_bytes(sample_file.read_bytes())

    main(Args(copied_sample))

    assert (tmp_path / "sample.csv").exists()