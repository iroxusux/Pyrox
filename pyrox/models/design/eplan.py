"""Eplan Design Utility Module
"""
from __future__ import annotations

import pandas as pd

from ...models.plc.plc import Controller
from ...services.xml import parse_xml


class EPlanDesignUtility:
    """Utility class for reading EPlan design specifications.
    These specifications are used to assist with generating a PLC controller, or other similar tasks.
    """

    def __init__(self,
                 data: dict[str, pd.DataFrame]) -> None:
        self._data = data
        self._modules_info = {}

    @classmethod
    def from_file(cls, file_location: str) -> 'EPlanDesignUtility':
        """Create an instance of EPlanDesignUtility from a file.

        Args:
            file_location (str): The path to the EPlan design file.

        Returns:
            EPlanDesignUtility: An instance of the utility class.
        """
        return cls(parse_xml(file_location))

    @property
    def cover_sheet(self) -> pd.DataFrame:
        """Return the cover sheet tab as a DataFrame."""
        return self.get_tab('CoverSheet')

    @property
    def cover_sheet_data(self) -> dict[str, pd.DataFrame]:
        """Return the cover sheet data as a dictionary."""
        return self.cover_sheet.iloc[14, 1]

    @property
    def ethernet(self) -> pd.DataFrame:
        """Return the Ethernet tab as a DataFrame."""
        return self.get_tab('Ethernet')

    @property
    def parts_data(self) -> pd.DataFrame:
        """Return the Parts Data tab as a DataFrame."""
        return self.get_tab('Parts_Data')

    @property
    def power_120vac(self) -> pd.DataFrame:
        """Return the 120VAC power tab as a DataFrame."""
        return self.get_tab('120v Power')

    @property
    def power_24vdc(self) -> pd.DataFrame:
        """Return the 24VDC power tab as a DataFrame."""
        return self.get_tab('24v Power')

    @property
    def power_480vac(self) -> pd.DataFrame:
        """Return the 480VAC power tab as a DataFrame."""
        return self.get_tab('480v Power')

    @property
    def safety_io(self) -> pd.DataFrame:
        """Return the Safety IO tab as a DataFrame."""
        return self.get_tab('Safety IO')

    @property
    def standard_io(self) -> pd.DataFrame:
        """Return the Standard IO tab as a DataFrame."""
        return self.get_tab('Standard IO')

    @property
    def tabs(self) -> list[str]:
        """Return a list of all tab (sheet) names in the parsed file."""
        return list(self._data.keys())

    def get_tab(self, tab_name: str) -> pd.DataFrame:
        """Return the DataFrame for a given tab name."""
        return self._data.get(tab_name)

    def find_modules_by_keyword(self, tab_name: str, keyword: str, column: str = None) -> pd.DataFrame:
        """
        Search for rows in a tab containing a specific keyword in a given column.
        If column is None, search all columns.
        """
        df = self.get_tab(tab_name)
        if df is None:
            return pd.DataFrame()
        if column and column in df.columns:
            mask = df[column].astype(str).str.contains(keyword, na=False, case=False)
        else:
            mask = df.apply(lambda row: row.astype(str).str.contains(keyword, na=False, case=False).any(), axis=1)
        found = df[mask]
        # Save found modules for later retrieval
        if tab_name not in self._modules_info:
            self._modules_info[tab_name] = []
        self._modules_info[tab_name].extend(found.to_dict('records'))
        return found

    def get_saved_modules(self, tab_name: str = None) -> list[dict]:
        """Retrieve previously saved module information."""
        if tab_name:
            return self._modules_info.get(tab_name, [])
        # Return all saved modules from all tabs
        all_modules = []
        for modules in self._modules_info.values():
            all_modules.extend(modules)
        return all_modules

    def create_controller(self, controller_kwargs: dict = None) -> Controller:
        """
        Create a PLC Controller object using the saved module information.
        Optionally pass additional kwargs to the Controller constructor.
        """
        controller_kwargs = controller_kwargs or {}
        meta_data = {'Modules': {'Module': self.get_saved_modules()}}
        controller_kwargs.setdefault('root_meta_data', {'RSLogix5000Content': {'Controller': meta_data}})
        return Controller(**controller_kwargs)

    @staticmethod
    def sheet_data(sheet: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """
        Convert a DataFrame representing a sheet into a dictionary format.
        This is useful for converting the sheet data into a format that can be used by the utility.
        """
        return {sheet.name: sheet} if hasattr(sheet, 'name') else {'Sheet': sheet}
