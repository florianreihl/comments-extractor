from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD

from comments_extractor import (
    get_files,
    extract_files,
    default_output_path,
    write_csv,
    resolve_separate_csv_paths,
)

ASSETS_DIR = Path(__file__).parent / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"

last_dir = Path.cwd()


def set_input_path(path):
    global last_dir

    path = Path(path)

    input_path.set(str(path))
    output_path.set(str(default_output_path(path)))

    last_dir = path if path.is_dir() else path.parent

    if path.is_dir():
        separate_checkbox.config(state="normal")
    else:
        separate_csvs.set(False)
        separate_checkbox.config(state="disabled")


def browse_file():
    path = filedialog.askopenfilename(
        title="Select a file",
        initialdir=last_dir,
        filetypes=[
            ("Supported files", "*.docx *.html *.htm"),
            ("Word files", "*.docx"),
            ("HTML files", "*.html *.htm"),
            ("All files", "*.*"),
        ],
    )

    if path:
        set_input_path(path)
        status_label.config(text="File selected.")


def browse_folder():
    path = filedialog.askdirectory(title="Select a folder", initialdir=last_dir)

    if path:
        set_input_path(path)
        status_label.config(text="Folder selected.")


def browse_output():
    global last_dir

    path = filedialog.asksaveasfilename(
        title="Save CSV file",
        initialdir=last_dir,
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
    )

    if path:
        output_path.set(path)
        last_dir = Path(path).parent


def handle_drop(event):
    path = event.data.strip()

    if path.startswith("{") and path.endswith("}"):
        path = path[1:-1]

    set_input_path(path)
    status_label.config(text="Input selected by drag and drop.")


def extract_comments():
    if not input_path.get():
        messagebox.showerror(
            "Missing input",
            "Please select or drag in a file or folder.",
        )
        return

    selected_input = Path(input_path.get())
    csv_path = Path(output_path.get()) if output_path.get() else default_output_path(selected_input)

    try:
        files = get_files(selected_input)

        progress_bar["value"] = 0
        progress_bar["maximum"] = max(len(files), 1)

        extract_button.config(state="disabled")
        status_label.config(text="Extracting comments...")
        root.update_idletasks()

        all_records, records_by_file, errors = extract_files(
            files,
            show_progress=False,
        )

        progress_bar["value"] = len(files)

        if separate_csvs.get() and selected_input.is_dir():
            paths, warnings = resolve_separate_csv_paths(files)

            for file, records in records_by_file.items():
                write_csv(records, paths[file])

            save_text = "Created one CSV per document."
            if warnings:
                save_text += "\n\n" + "\n".join(warnings)
        else:
            write_csv(all_records, csv_path)

            save_text = f"Saved to {csv_path}."

        comment_count = len(all_records)
        file_count = len(files)
        failed_count = len(errors)
        succeeded_count = file_count - failed_count

        status_label.config(
            text=(
                f"{comment_count} comments extracted from {succeeded_count}/{file_count} document(s). {save_text}"
                + (f" {failed_count} file(s) failed." if failed_count else "")
            )
        )

        if errors:
            failure_lines = "\n".join(f"- {file.name}: {message}" for file, message in errors)
            messagebox.showwarning(
                "Completed with errors",
                f"{comment_count} comments extracted from {succeeded_count}/{file_count} document(s).\n\n"
                f"{save_text}\n\n"
                f"The following file(s) could not be processed:\n{failure_lines}",
            )
        else:
            messagebox.showinfo(
                "Success",
                f"{comment_count} comments extracted from {file_count} document(s).\n\n{save_text}",
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
root.geometry("720x500")
root.resizable(False, False)

input_path = tk.StringVar()
output_path = tk.StringVar()
separate_csvs = tk.BooleanVar(value=False)

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

separate_checkbox = tk.Checkbutton(
    output_frame,
    text="Create one CSV per document (folders only)",
    variable=separate_csvs,
)
separate_checkbox.pack(anchor="w", pady=(6, 0))

separate_checkbox.config(state="disabled")

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