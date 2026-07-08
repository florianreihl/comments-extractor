# Comments Extractor

Extract comments from Microsoft Word (`.docx`) documents and Google Docs HTML exports (`.html`/`.htm`) into a CSV file.

Originally developed for exporting qualitative coding comments from interview transcripts, but can be used with any document containing comments.

## Features

- Microsoft Word (`.docx`) support
- Google Docs HTML export support
- Automatic file type detection
- Process a single file or a directory
- Option to export one combined CSV or one CSV per document
- Optional progress/error log files, plus a quiet mode for the CLI
- Graphical interface with drag-and-drop support
- Command-line interface
- CSV export

## Installation

Clone the repository and install the dependencies.

```bash
git clone https://github.com/YOUR_USERNAME/comments-extractor.git
cd comments-extractor

pip install -r requirements.txt
```

## Usage

### GUI

Launch the application:

```bash
python app.py
```

Select or drag a supported file or folder into the application, choose an output location, and click **Extract Comments**. If any files fail to process, a dialog will list which ones and why.

When a folder is selected, a **"Create one CSV per document"** checkbox becomes available. Leave it unchecked to combine all comments into a single CSV, or check it to save a separate CSV alongside each source document.

### CLI

Single file:

```bash
python comments_extractor.py -d Transcript.docx -s comments.csv
```

Directory (combined CSV):

```bash
python comments_extractor.py -d ./documents -s comments.csv
```

Directory (one CSV per document):

```bash
python comments_extractor.py -d ./documents --separate
```

With `--separate`, each source document gets its own CSV saved next to it (e.g. `Transcript.docx` → `Transcript.csv`), and the `-s`/`--save` option is ignored. If two files in the same folder would produce the same CSV name (e.g. `sample.docx` and `sample.html` both wanting `sample.csv`), the colliding ones are saved as `sample.docx.csv` and `sample.html.csv` instead of overwriting each other, and a warning is logged.

Quiet mode (no terminal output):

```bash
python comments_extractor.py -d ./documents -s comments.csv -q
```

By default nothing is written to disk beyond the CSV output — progress and errors just print to the terminal. Add `--log-dir` to also save `progress.log` and `errors.log` there:

```bash
python comments_extractor.py -d ./documents -s comments.csv --log-dir ./logs
```

`-q`/`--quiet` only suppresses terminal output; if `--log-dir` is set, the log files are still written.

## Google Docs

Export the document as:

**File → Download → Web Page (.html, zipped)**

Extract the archive and use the exported `.html` file.

## Output

The generated CSV contains:

| Column | Description |
|---------|-------------|
| ID | Comment identifier |
| COMMENT_TEXT | Comment text |
| SPAN_TEXT | Associated text |
| FILENAME | Source document |

## Tests

Run:

```bash
pytest
```

## Repository Structure

```text
.
├── app.py
├── comments_extractor.py
├── requirements.txt
├── assets/
├── tests/
└── README.md
```

## License

MIT License.