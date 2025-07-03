# filepath: tests/test_eplan.py

import unittest
from unittest.mock import patch, MagicMock

import pandas as pd
from pyrox.models.design.eplan import EPlanDesignUtility


UNITTEST_XML_FILE = r'docs\_design_util.xlsm'


class TestEPlanDesignUtility(unittest.TestCase):
    def setUp(self):
        # Create dummy data
        self.utility = EPlanDesignUtility.from_file(UNITTEST_XML_FILE)

    def test_tabs_property(self):
        self.assertTrue('CoverSheet' in self.utility.tabs)
        self.assertTrue('480v Power' in self.utility.tabs)
        self.assertTrue('120v Power' in self.utility.tabs)
        self.assertTrue('24v Power' in self.utility.tabs)
        self.assertTrue('Ethernet' in self.utility.tabs)
        self.assertTrue('Safety IO' in self.utility.tabs)
        self.assertTrue('Standard IO' in self.utility.tabs)

    def test_get_tab(self):
        self.assertIsNotNone(self.utility.get_tab('CoverSheet'))
        self.assertIsNone(self.utility.get_tab('NonExistent'))

    def test_sheet_data(self):
        cover_sheet_data = self.utility.sheet_data(self.utility.cover_sheet)
        items = cover_sheet_data.get('Sheet', None)
        self.assertIsNotNone(items)
        self.assertIsInstance(cover_sheet_data, dict)
        self.assertIn('Sheet', cover_sheet_data)
        self.assertIsInstance(cover_sheet_data['Sheet'], pd.DataFrame)

    def test_sheet_data_extraction(self):
        for x in self.utility.cover_sheet.columns:
            y = self.utility.cover_sheet[x]
            self.assertIsInstance(y, pd.Series)
            print(f"Column: {x}, Value: {self.utility.cover_sheet[x]}")
            self.assertIsInstance(self.utility.cover_sheet[x], pd.Series)
        cover_sheet_data = self.utility.cover_sheet_data
        self.assertIsInstance(cover_sheet_data, pd.DataFrame)

    def test_find_modules_by_keyword(self):
        found = self.utility.find_modules_by_keyword('Sheet1', 'ModuleA', column='Name')
        self.assertEqual(found.iloc[0]['Name'], 'ModuleA')
        # Should save found modules
        saved = self.utility.get_saved_modules('Sheet1')
        self.assertTrue(any(m['Name'] == 'ModuleA' for m in saved))

    @patch('pyrox.models.design.eplan.Controller')
    def test_create_controller(self, mock_controller):
        # Save some modules first
        self.utility.find_modules_by_keyword('Sheet1', 'ModuleA', column='Name')
        controller_instance = MagicMock()
        mock_controller.return_value = controller_instance
        result = self.utility.create_controller()
        mock_controller.assert_called_once()
        self.assertIs(result, controller_instance)


if __name__ == '__main__':
    unittest.main()
