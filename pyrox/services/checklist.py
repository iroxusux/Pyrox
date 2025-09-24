from typing import Optional
from pyrox.services.file import transform_file_to_dict


def compile_checklist_from_md_file(
    file_path: Optional[str] = None
) -> dict:
    """Compile a checklist from a markdown file.

    Args:
        file_path (str): Path to the markdown file."""
    checklist = transform_file_to_dict(file_path)
    return checklist
