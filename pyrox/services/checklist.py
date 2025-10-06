from typing import Optional
from pyrox.models.eplan import project as proj
from pyrox.services import env
from pyrox.services.file import transform_file_to_dict
from pyrox.services.logging import log


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


def _finalize_checklist_checks(checklist: dict) -> None:
    """Helper function to log test information."""
    if checklist is None:
        raise ValueError("Checklist compilation error occured!")
    log().info('Checklist template generated')
    log().info(f'- Tests generated: {len(checklist["tests"])}')
    for test_name, content in checklist['tests'].items():
        log().info(f'  - {test_name}: {len(content)} steps')


def _compile_hmi_checklist_from_eplan_project(
    project: proj.EplanProject,
    template: dict
) -> dict:
    pass  # Placeholder for future implementation
    return {}


def compile_checklist_from_eplan_project(
    project: proj.EplanProject,
    template: dict
) -> dict:
    project_checklist = {}
    project_checklist['HMI'] = _compile_hmi_checklist_from_eplan_project(project, template)
    return project_checklist


def get_checklist_template_from_md_file(
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
    _finalize_checklist_checks(checklist)
    return checklist


def get_controls_template() -> dict:
    template_path = env.get_env('CHECKLIST_TEMPLATE_FILE')
    if not template_path:
        raise ValueError('No controls template file path set in environment variable CHECKLIST_TEMPLATE_FILE')

    log(__name__).info(f'Loading controls template from {template_path}')
    controls_template = get_checklist_template_from_md_file(template_path)
    if controls_template is None:
        raise ValueError(f'Could not load controls template from {template_path}')
    return controls_template
