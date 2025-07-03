"""handles XML parsing and validation for Pyrox."""

from __future__ import annotations

import pandas as pd


def parse_xml(file_location: str) -> dict[str, pd.DataFrame]:
    """Parse an XML file and return its content as a dictionary.

    Args:
        file_location (str): The path to the XML file.

    Returns:
        dict[str, Any]: Parsed XML content as a dictionary.
    """
    return pd.read_excel(file_location, sheet_name=None)
