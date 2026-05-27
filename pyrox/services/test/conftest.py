import pathlib
import pytest
from pyrox.services.xml import dict_from_xml_file

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

FIXTURES_DIR: pathlib.Path = pathlib.Path(__file__).parents[2] / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def fixture_dir() -> pathlib.Path:
    """Absolute path to the shared fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def xml_fixture_path() -> pathlib.Path:
    path = FIXTURES_DIR / "special_xml.L5X"
    if not path.exists():
        pytest.fail(f"xml fixture not found: {path}")
    return path


@pytest.fixture(scope="session")
def xml_fixture_dict(xml_fixture_path: pathlib.Path) -> dict:
    dict = dict_from_xml_file(str(xml_fixture_path))
    assert dict is not None, f"Failed to parse XML fixture: {xml_fixture_path}"
    return dict
