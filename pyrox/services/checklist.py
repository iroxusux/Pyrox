from typing import Optional
from pyrox.services.file import transform_file_to_dict


def _categorize_sections_by_header(lines: list, header: str) -> dict:
    """Helper function to categorize sections by header."""
    categorized = {}
    current_section = None
    for line in lines:
        if line.startswith(header):
            current_section = line.strip(header).strip()
            categorized[current_section] = {'lines': []}
        elif current_section:
            categorized[current_section]['lines'].append(line)
    return categorized


def _get_all_tests(sections: dict) -> None:
    """Helper function to get all tests from sections."""
    for section, content in sections.items():
        sections[section]['tests'] = _get_sections_tests(content['lines'])


def _get_sections_tests(lines: list) -> dict:
    """Helper function to get sections that contain tests."""
    tests = {}
    current_test = None
    for line in lines:
        if line.strip() == '':
            current_test = None
        else:
            current_test = line.strip()
            tests[current_test] = {'lines': []}
    return tests


def _strip_new_lines_from_list(lines: list) -> list:
    """Helper function to strip new lines from a list of strings."""
    return [line for line in lines if line.strip() != '']


def compile_checklist_from_md_file(
    file_path: Optional[str] = None
) -> dict:
    """Compile a checklist from a markdown file.

    Args:
        file_path (str): Path to the markdown file."""
    checklist = transform_file_to_dict(file_path)

    checklist['sections'] = _categorize_sections_by_header(
        checklist['content'], '#####'  # Default header used when developed template
    )

    _get_all_tests(checklist['sections'])
    return checklist
