# Comments Extractor

Extract comments from Microsoft Word (`.docx`) documents and Google Docs HTML exports into a CSV file.

Originally developed for exporting qualitative coding comments from interview transcripts, but can be used with any document containing comments.

## Features

- Extract comments from Microsoft Word (`.docx`) documents.
- Extract comments from Google Docs HTML exports (`.html` / `.htm`).
- Process a single file or an entire directory.
- Automatically detect the input file type.
- Export comments and associated text to a CSV file.

## Installation

Install the required packages:

```bash
pip install -r requirements.txt
```

Or install them individually:

```bash
pip install pandas beautifulsoup4 tqdm pytest
```

## Usage

### Process a single file

Microsoft Word:

```bash
python comments_extractor.py -d Transcript.docx -s comments.csv
```

Google Docs HTML export:

```bash
python comments_extractor.py -d Interview.html -s comments.csv
```

### Process a directory

```bash
python comments_extractor.py -d ./documents -s comments.csv
```

All supported `.docx`, `.html`, and `.htm` files in the directory will be processed.

## Output

The generated CSV contains the following columns:

| Column | Description |
|---------|-------------|
| ID | Internal comment identifier |
| COMMENT_TEXT | Comment text |
| SPAN_TEXT | Text associated with the comment |
| FILENAME | Source document |

Example:

| ID | COMMENT_TEXT | SPAN_TEXT | FILENAME |
|----|--------------|-----------|----------|
| 0 | This is a test comment. | sample document | sample.docx |

## Google Docs

Export the document as:

**File → Download → Web Page (.html, zipped)**

Extract the downloaded archive and use the `.html` file.

## Running the Tests

Run the test suite:

```bash
pytest
```

or

```bash
pytest -v
```

The tests verify that the script:

- runs successfully
- creates a CSV file
- produces a CSV readable by pandas
- generates the expected output columns
- extracts comments from the sample document

## Repository Structure

```text
.
├── comments_extractor.py
├── README.md
├── requirements.txt
├── tests
│   ├── test_comments_extractor.py
│   └── data
│       ├── sample.docx
│       └── sample.html
```

## Notes

- Supported input formats: `.docx`, `.html`, and `.htm`.
- Documents without comments produce an empty CSV.
- Existing output files are overwritten.

## License

MIT License.