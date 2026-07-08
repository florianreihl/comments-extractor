from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD
import pandas as pd

from comments_extractor import get_files, extract_comment_data


COLUMNS = ["ID", "COMMENT_TEXT", "SPAN_TEXT", "FILENAME"]
ASSETS_DIR = Path(__file__).parent / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"


def browse_file():
    path = filedialog.askopenfilename(
        title="Select a file",
        filetypes=[
            ("Supported files", "*.docx *.html *.htm"),
            ("Word files", "*.docx"),
            ("HTML files", "*.html *.htm"),
            ("All files", "*.*"),
        ],
    )

    if path:
        input_path.set(path)
        status_label.config(text="File selected.")


def browse_folder():
    path = filedialog.askdirectory(title="Select a folder")

    if path:
        input_path.set(path)
        status_label.config(text="Folder selected.")


def browse_output():
    path = filedialog.asksaveasfilename(
        title="Save CSV file",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
    )

    if path:
        output_path.set(path)


def handle_drop(event):
    path = event.data.strip()

    if path.startswith("{") and path.endswith("}"):
        path = path[1:-1]

    input_path.set(path)
    status_label.config(text="Input selected by drag and drop.")


def extract_comments():
    if not input_path.get():
        messagebox.showerror("Missing input", "Please select or drag in a file or folder.")
        return

    if not output_path.get():
        messagebox.showerror("Missing output", "Please choose where to save the CSV.")
        return

    try:
        files = get_files(Path(input_path.get()))

        progress_bar["value"] = 0
        progress_bar["maximum"] = max(len(files), 1)

        all_records = []

        extract_button.config(state="disabled")
        status_label.config(text="Starting extraction...")
        root.update_idletasks()

        for index, file in enumerate(files, start=1):
            status_label.config(text=f"Processing {file.name}...")
            root.update_idletasks()

            records = extract_comment_data(file)
            all_records.extend(records)

            progress_bar["value"] = index
            root.update_idletasks()

        df = pd.DataFrame.from_records(data=all_records, columns=COLUMNS)
        df.to_csv(output_path.get(), index=False)

        comment_count = len(all_records)
        file_count = len(files)

        status_label.config(
            text=f"{comment_count} comments extracted from {file_count} document(s)."
        )

        messagebox.showinfo(
            "Success",
            f"{comment_count} comments extracted from {file_count} document(s).",
        )

    except Exception as error:
        status_label.config(text="Error.")
        messagebox.showerror("Error", str(error))

    finally:
        extract_button.config(state="normal")


root = TkinterDnD.Tk()

if ICON_PATH.exists():
    app_icon = tk.PhotoImage(file=ICON_PATH)
    root.iconphoto(True, app_icon)

root.title("Comments Extractor")
root.geometry("720x430")
root.resizable(False, False)

input_path = tk.StringVar()
output_path = tk.StringVar()

main_frame = tk.Frame(root, padx=24, pady=20)
main_frame.pack(fill="both", expand=True)

title_label = tk.Label(
    main_frame,
    text="Comments Extractor",
    font=("Arial", 20, "bold"),
)
title_label.pack(anchor="w")

subtitle_label = tk.Label(
    main_frame,
    text="Extract Word and Google Docs comments into a CSV file.",
)
subtitle_label.pack(anchor="w", pady=(2, 16))

drop_label = tk.Label(
    main_frame,
    text="Drop a .docx, .html, .htm file, or folder here",
    relief="groove",
    height=4,
)
drop_label.pack(fill="x", pady=(0, 12))

drop_label.drop_target_register(DND_FILES)
drop_label.dnd_bind("<<Drop>>", handle_drop)

browse_frame = tk.Frame(main_frame)
browse_frame.pack(fill="x", pady=(0, 12))

file_button = tk.Button(
    browse_frame,
    text="Browse File",
    command=browse_file,
    width=18,
)
file_button.pack(side="left", padx=(0, 8))

folder_button = tk.Button(
    browse_frame,
    text="Browse Folder",
    command=browse_folder,
    width=18,
)
folder_button.pack(side="left")

input_label = tk.Label(main_frame, text="Selected input:")
input_label.pack(anchor="w")

input_entry = tk.Entry(main_frame, textvariable=input_path)
input_entry.pack(fill="x", pady=(2, 12))

output_frame = tk.Frame(main_frame)
output_frame.pack(fill="x", pady=(0, 12))

output_label = tk.Label(output_frame, text="Output CSV:")
output_label.pack(anchor="w")

output_row = tk.Frame(output_frame)
output_row.pack(fill="x", pady=(2, 0))

output_entry = tk.Entry(output_row, textvariable=output_path)
output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

output_button = tk.Button(
    output_row,
    text="Save As...",
    command=browse_output,
    width=14,
)
output_button.pack(side="left")

progress_bar = ttk.Progressbar(
    main_frame,
    orient="horizontal",
    mode="determinate",
)
progress_bar.pack(fill="x", pady=(4, 12))

extract_button = tk.Button(
    main_frame,
    text="Extract Comments",
    command=extract_comments,
    height=2,
    width=22,
)
extract_button.pack(pady=(0, 12))

status_label = tk.Label(
    main_frame,
    text="Select or drag in a file/folder to begin.",
)
status_label.pack(anchor="w")

root.mainloop()