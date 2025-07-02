"""testing module for services
    """
from .plc_services import (
    cdata,
    l5x_dict_from_file,
    dict_to_xml_file,
    get_rung_text,
    get_xml_string_from_file,
    preprocessor
)


from unittest.mock import patch
import unittest
import lxml
import lxml.etree as ET


DUPS_TEST_FILE = r'docs\controls\_test_duplicate_coils.L5X'
GM_TEST_FILE = r'docs\controls\_test_gm.L5X'
ROOT_TEST_FILE = r'docs\controls\root.L5X'


class TestCData(unittest.TestCase):
    def test_cdata(self):
        result = cdata("test")
        self.assertEqual(result, "<![CDATA[test]]>")


class TestL5XDictFromFile(unittest.TestCase):
    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            l5x_dict_from_file("non_existent_file.L5X")

    def test_invalid_file_extension(self):
        with self.assertRaises(ValueError):
            l5x_dict_from_file("invalid_file.txt")

    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    def test_parse_error(self, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parse.side_effect = lxml.etree.ParseError
        result = l5x_dict_from_file("invalid_file.L5X")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    def test_unexpected_error(self, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parse.side_effect = Exception("Unexpected error")
        result = l5x_dict_from_file("unexpected_error.L5X")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    @patch("lxml.etree.XMLParser")
    @patch("xmltodict.parse")
    def test_successful_parse(self, mock_xmltodict_parse, mock_parser, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parser.return_value = lxml.etree.XMLParser(strip_cdata=False)
        mock_parse.return_value.getroot.return_value = lxml.etree.Element("root")
        mock_parse.return_value.getroot.return_value.text = "<root></root>"
        mock_xmltodict_parse.return_value = {"root": {}}
        result = l5x_dict_from_file("valid_file.L5X")
        self.assertEqual(result, {"root": {}})

    def test_all_base_files(self):
        from ..models.plc import BASE_FILES
        for file in BASE_FILES:
            with self.subTest(file=file):
                result = l5x_dict_from_file(file)
                self.assertIsInstance(result, dict)
                self.assertTrue(len(result) > 0, f"File {file} should not be empty.")


class TestDictToControllerFile(unittest.TestCase):
    @patch("pyrox.services.plc_services.save_file")
    @patch("xmltodict.unparse")
    def test_dict_to_controller_file(self, mock_unparse, mock_save_file):
        controller = {"root": {}}
        file_location = "controller.L5X"
        dict_to_xml_file(controller, file_location)
        mock_unparse.assert_called_once_with(controller, preprocessor=preprocessor, pretty=True)
        mock_save_file.assert_called_once()


class TestGetRungText(unittest.TestCase):
    def test_get_rung_text_with_text(self):
        rung = ET.Element("Rung")
        text_element = ET.SubElement(rung, "Text")
        text_element.text = "Test text"
        result = get_rung_text(rung)
        self.assertEqual(result, "Test text")

    def test_get_rung_text_with_comment(self):
        rung = ET.Element("Rung")
        comment_element = ET.SubElement(rung, "Comment")
        comment_element.text = "Test comment"
        result = get_rung_text(rung)
        self.assertEqual(result, "Test comment")

    def test_get_rung_text_no_description(self):
        rung = ET.Element("Rung")
        result = get_rung_text(rung)
        self.assertEqual(result, "No description available")


class TestGetXmlStringFromFile(unittest.TestCase):
    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    @patch("lxml.etree.XMLParser")
    def test_get_xml_string_from_file(self, mock_parser, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parser.return_value = lxml.etree.XMLParser(strip_cdata=False)
        mock_parse.return_value.getroot.return_value = lxml.etree.Element("root")
        mock_parse.return_value.getroot.return_value.text = "<root></root>"
        result = get_xml_string_from_file("valid_file.L5X")
        self.assertEqual(result, "<root>&lt;root&gt;&lt;/root&gt;</root>")


class TestPreprocessor(unittest.TestCase):
    def test_preprocessor_with_cdata(self):
        key = "Comment"
        value = "Test comment"
        result_key, result_value = preprocessor(key, value)
        self.assertEqual(result_key, key)
        self.assertEqual(result_value, "<![CDATA[Test comment]]>")


class TestFindAndInstantiateClass(unittest.TestCase):
    def test_find_and_instantiate_class(self):
        from .task_services import find_and_instantiate_class
        from pyrox.models import ApplicationTask

        my_objects = find_and_instantiate_class(directory_path=r"pyrox\\tasks\\builtin",
                                                class_name="ApplicationTask",
                                                as_subclass=True,
                                                ignoring_classes=["ApplicationTask", "AppTask"],
                                                parent_class=ApplicationTask,
                                                application=None)
        self.assertIsNotNone(my_objects)
        self.assertTrue(len(my_objects) >= 3)
        self.assertTrue(hasattr(my_objects[0], "application"))


if __name__ == '__main__':
    unittest.main()
