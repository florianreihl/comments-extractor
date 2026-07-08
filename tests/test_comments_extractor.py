import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from comments_extractor import main


class Args:
    def __init__(self, data, save=None, separate=False, log_dir=None):
        self.data = Path(data)
        self.save = save
        self.separate = separate
        self.log_dir = log_dir


def test_sample_file_extracts_comment(tmp_path):
    sample_file = Path(__file__).parent / "data" / "sample.docx"
    output_csv = tmp_path / "comments.csv"

    main(Args(sample_file, output_csv, log_dir=tmp_path))

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

    main(Args(copied_sample, separate=True, log_dir=tmp_path))

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

    main(Args(copied_sample, log_dir=tmp_path))

    assert (tmp_path / "sample.csv").exists()


def test_separate_csv_duplicate_stem_names(tmp_path):
    """Two files that share a name but differ by extension (sample.docx
    and sample.html) would both naively resolve to sample.csv. Make sure
    the collision is caught and both get renamed instead of one silently
    overwriting the other.
    """
    sample_file = Path(__file__).parent / "data" / "sample.docx"

    docx_copy = tmp_path / "sample.docx"
    docx_copy.write_bytes(sample_file.read_bytes())

    html_copy = tmp_path / "sample.html"
    html_copy.write_text(
        """
        <html>
        <body>
        <p>
        <span>the highlighted phrase</span>
        <sup><a id="cmnt_ref1" href="#cmnt1"></a></sup>
        </p>
        <div>
        <a id="cmnt1" href="#cmnt_ref1">
        <span>This is a comment from the html sample.</span>
        </a>
        </div>
        </body>
        </html>
        """,
        encoding="utf-8",
    )

    main(Args(tmp_path, separate=True, log_dir=tmp_path))
    
    assert not (tmp_path / "sample.csv").exists()

    docx_csv = tmp_path / "sample.docx.csv"
    html_csv = tmp_path / "sample.html.csv"

    assert docx_csv.exists()
    assert html_csv.exists()

    docx_df = pd.read_csv(docx_csv)
    assert len(docx_df) == 1
    assert docx_df.iloc[0]["COMMENT_TEXT"] == "This is a test comment."
    assert docx_df.iloc[0]["SPAN_TEXT"] == "sample document"
    assert docx_df.iloc[0]["FILENAME"] == "sample.docx"

    html_df = pd.read_csv(html_csv)
    assert len(html_df) == 1
    assert html_df.iloc[0]["COMMENT_TEXT"] == "This is a comment from the html sample."
    assert html_df.iloc[0]["SPAN_TEXT"] == "the highlighted phrase"
    assert html_df.iloc[0]["FILENAME"] == "sample.html"