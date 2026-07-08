# Comments Extractor

Extract comments from Microsoft Word (`.docx`) documents and Google Docs HTML exports (`.html`/`.htm`) into a CSV file.

Originally developed for exporting qualitative coding comments from interview transcripts, but can be used with any document containing comments.

## Features

- Microsoft Word (`.docx`) support
- Google Docs HTML export support
- Automatic file type detection
- Process a single file or a directory
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

Select or drag a supported file or folder into the application, choose an output location, and click **Extract Comments**.

### CLI

Single file:

```bash
python comments_extractor.py -d Transcript.docx -s comments.csv
```

Directory:

```bash
python comments_extractor.py -d ./documents -s comments.csv
```

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