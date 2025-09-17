"""Archive services.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Union
import py7zr


def decompress_7zip_to_dict(archive_path: str) -> Dict[str, bytes]:
    """Decompress 7zip file into dictionary with filename -> content mapping."""
    archive_dict = {}

    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        # Extract all files to memory
        extracted = archive.readall()

        for filename, bio in extracted.items():
            # bio is a BytesIO object
            archive_dict[filename] = bio.getvalue()

    return archive_dict


def decompress_7zip_filtered(archive_path: str, extensions: list = None) -> Dict[str, Union[str, bytes]]:
    """Decompress 7zip with filtering and text conversion."""
    archive_dict = {}
    text_extensions = {'.txt', '.xml', '.json', '.csv', '.log'} if not extensions else set(extensions)

    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        extracted = archive.readall()

        for filename, bio in extracted.items():
            file_path = Path(filename)
            content = bio.getvalue()

            # Convert text files to strings
            if file_path.suffix.lower() in text_extensions:
                try:
                    # Try different encodings
                    for encoding in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            archive_dict[filename] = content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # If all encodings fail, store as bytes
                        archive_dict[filename] = content
                except Exception:
                    archive_dict[filename] = content
            else:
                # Store binary files as bytes
                archive_dict[filename] = content

    return archive_dict
