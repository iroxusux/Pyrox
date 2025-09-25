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


def _compile_checklist_from_metadata(
    checklist_meta: dict
) -> dict:
    """Helper function to compile checklist from metadata.
    """
    checklist = {
        'title': checklist_meta.get('title', 'N/A'),
        'description': checklist_meta.get('description', 'N/A'),
        'tests': {},  # This will be populated later
        'file_path': checklist_meta.get('file_path', 'N/A'),
        'line_count': checklist_meta.get('line_count', 0),
        'content_preview': checklist_meta.get('content_preview', []),
        'content': checklist_meta.get('content', [])
    }

    for section, content in checklist_meta['sections'].items():
        checklist['tests'][section] = content.get('tests', {})

    return checklist


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
            if not current_test:
                current_test = line.strip()
                tests[current_test] = {'lines': []}
            if not current_test:
                raise ValueError("Test name cannot be empty.")
            tests[current_test]['lines'].append(line)
    return tests


def compile_checklist_from_md_file(
    file_path: Optional[str] = None
) -> dict:
    """Compile a checklist from a markdown file.

    Args:
        file_path (str): Path to the markdown file.

    Returns:
        dict: Compiled checklist data.
    """
    checklist_meta = transform_file_to_dict(file_path)

    checklist_meta['sections'] = _categorize_sections_by_header(
        checklist_meta['content'], '#####'  # Default header used when developed template
    )

    _get_all_tests(checklist_meta['sections'])
    checklist = _compile_checklist_from_metadata(checklist_meta)
    return checklist
