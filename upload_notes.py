"""
CREST Academy — Primary Notes Uploader
----------------------------------------
This script walks through the "notes" folder (Standard 5-8, each containing
subject PDFs), uploads every PDF to Cloudinary, then adds a matching entry
for each one into your JSONBin "books" dataset so they show up automatically
inside index.html under Primary School -> Standard X -> Subject -> Notes.

HOW TO USE:
1. Put this script in a folder together with the "notes" folder
   (notes/Standard 5/Agriculture.pdf, notes/Standard 6/..., etc.)
2. Open a terminal in that folder and run:
     pip install requests
     python upload_notes.py
3. Wait for it to finish - it will print progress for every file.
4. Refresh index.html (or your live site) and check Primary School -> Standard 5/6/7/8.

You do NOT need to touch JSONBin or Cloudinary manually - this script does it all.
"""

import os
import requests

# ── Same credentials your index.html / admin.html already use ──────────────
API_KEY = "$2a$10$q1K8WzlWXgpkdX5BYcLBfuiYIdv7ZrDcy2OjEiGlXdWC2Y5/CB7e6"
BIN_ID = "6a3e2279da38895dfe014a42"
BASE_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"

CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dfrnpdnld/auto/upload"
CLOUDINARY_PRESET = "taydayo"

NOTES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes")


def upload_to_cloudinary(filepath):
    """Uploads a single file to Cloudinary and returns its public URL."""
    with open(filepath, "rb") as f:
        files = {"file": f}
        data = {"upload_preset": CLOUDINARY_PRESET}
        resp = requests.post(CLOUDINARY_URL, files=files, data=data)
    resp.raise_for_status()
    return resp.json()["secure_url"]


def get_current_books():
    """Fetches the current books array from JSONBin so we don't overwrite it."""
    resp = requests.get(
        f"{BASE_URL}/latest",
        headers={"X-Master-Key": API_KEY, "X-Bin-Meta": "false"},
    )
    resp.raise_for_status()
    record = resp.json()
    return record if isinstance(record, dict) else {"books": [], "students": []}


def save_books(record):
    """Writes the full updated record back to JSONBin."""
    resp = requests.put(
        BASE_URL,
        headers={
            "X-Master-Key": API_KEY,
            "Content-Type": "application/json",
        },
        json=record,
    )
    resp.raise_for_status()


def main():
    if not os.path.isdir(NOTES_DIR):
        print(f"ERROR: Could not find the 'notes' folder next to this script.")
        print(f"Expected it at: {NOTES_DIR}")
        return

    print("Fetching your current library data from JSONBin...")
    record = get_current_books()
    record.setdefault("books", [])
    existing_titles = {(b.get("className"), b.get("subject")) for b in record["books"]}

    added = 0
    skipped = 0

    for standard_folder in sorted(os.listdir(NOTES_DIR)):
        standard_path = os.path.join(NOTES_DIR, standard_folder)
        if not os.path.isdir(standard_path):
            continue

        for filename in sorted(os.listdir(standard_path)):
            if not filename.lower().endswith(".pdf"):
                continue

            subject = os.path.splitext(filename)[0]  # e.g. "Agriculture"
            class_name = standard_folder  # e.g. "Standard 5"

            if (class_name, subject) in existing_titles:
                print(f"SKIP (already added): {class_name} - {subject}")
                skipped += 1
                continue

            filepath = os.path.join(standard_path, filename)
            print(f"Uploading: {class_name} - {subject} ...")
            try:
                url = upload_to_cloudinary(filepath)
            except Exception as e:
                print(f"  FAILED to upload {filepath}: {e}")
                continue

            record["books"].append({
                "title": f"{class_name} {subject} Notes",
                "level": "primary",
                "className": class_name,
                "subject": subject,
                "type": "Notes",
                "syllabus": "National",
                "link": url,
            })
            added += 1
            print(f"  Done -> {url}")

    if added == 0:
        print("\nNothing new to add.")
        return

    print(f"\nSaving {added} new note(s) to JSONBin (skipped {skipped} already present)...")
    save_books(record)
    print("All done! Refresh your site and check Primary School -> Standard 5/6/7/8.")


if __name__ == "__main__":
    main()
