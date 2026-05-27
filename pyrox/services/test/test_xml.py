"""Comprehensive pytest tests for pyrox.services.xml."""

import pathlib
import pytest
from pyrox.services.xml import dict_from_xml_file, is_valid_xml_file, xml_file_from_dict


# ---------------------------------------------------------------------------
# dict_from_xml_file — fixture-based integration tests
# ---------------------------------------------------------------------------

class TestDictFromXmlFileFixture:
    """Tests using the session-scoped special_xml.L5X fixture."""

    def test_returns_dict(self, xml_fixture_dict: dict) -> None:
        assert isinstance(xml_fixture_dict, dict)

    def test_top_level_key_is_rsx_content(self, xml_fixture_dict: dict) -> None:
        assert 'RSLogix5000Content' in xml_fixture_dict

    def test_controller_present(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        assert controller is not None

    def test_controller_name(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        assert controller['@Name'] == 'Base'

    def test_controller_processor_type(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        assert controller['@ProcessorType'] == '1756-L83ES'

    def test_programs_present(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        programs = controller['Programs']['Program']
        assert programs is not None

    def test_standard_program_exists(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        programs = controller['Programs']['Program']
        names = [p['@Name'] for p in programs]
        assert 'StandardProgram' in names

    def test_safety_program_exists(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        programs = controller['Programs']['Program']
        names = [p['@Name'] for p in programs]
        assert 's_SafetyProgram' in names

    def test_cdata_rung_text_preserved(self, xml_fixture_dict: dict) -> None:
        """CDATA content in rung Text elements must survive the round-trip."""
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        programs = controller['Programs']['Program']
        standard = next(p for p in programs if p['@Name'] == 'StandardProgram')
        rung = standard['Routines']['Routine']['RLLContent']['Rung']
        assert 'NOP' in rung['Text']

    def test_modules_present(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        modules = controller['Modules']['Module']
        assert modules is not None

    def test_local_module_name(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        module = controller['Modules']['Module']
        # single module may come back as a dict rather than a list
        if isinstance(module, list):
            names = [m['@Name'] for m in module]
            assert 'Local' in names
        else:
            assert module['@Name'] == 'Local'

    def test_tasks_present(self, xml_fixture_dict: dict) -> None:
        controller = xml_fixture_dict['RSLogix5000Content']['Controller']
        tasks = controller['Tasks']['Task']
        assert tasks is not None

    def test_schema_revision_attribute(self, xml_fixture_dict: dict) -> None:
        content = xml_fixture_dict['RSLogix5000Content']
        assert content['@SchemaRevision'] == '1.0'

    def test_path_object_accepted(self, xml_fixture_path: pathlib.Path) -> None:
        """dict_from_xml_file must accept a pathlib.Path, not just str."""
        result = dict_from_xml_file(xml_fixture_path)
        assert isinstance(result, dict)

    def test_str_path_accepted(self, xml_fixture_path: pathlib.Path) -> None:
        result = dict_from_xml_file(str(xml_fixture_path))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# dict_from_xml_file — error / edge-case unit tests
# ---------------------------------------------------------------------------

class TestDictFromXmlFileErrors:

    def test_missing_file_raises_file_not_found(self, tmp_path: pathlib.Path) -> None:
        missing = str(tmp_path / 'does_not_exist.xml')
        with pytest.raises(FileNotFoundError):
            dict_from_xml_file(missing)

    def test_invalid_xml_returns_none(self, tmp_path: pathlib.Path) -> None:
        bad_xml = tmp_path / 'bad.xml'
        bad_xml.write_text('<<not valid xml>>', encoding='utf-8')
        result = dict_from_xml_file(str(bad_xml))
        assert result is None

    def test_empty_xml_returns_none(self, tmp_path: pathlib.Path) -> None:
        empty = tmp_path / 'empty.xml'
        empty.write_bytes(b'')
        result = dict_from_xml_file(str(empty))
        assert result is None

    def test_minimal_valid_xml_parsed(self, tmp_path: pathlib.Path) -> None:
        minimal = tmp_path / 'minimal.xml'
        minimal.write_text('<root><child key="val"/></root>', encoding='utf-8')
        result = dict_from_xml_file(str(minimal))
        assert result is not None
        assert 'root' in result

    def test_cdata_empty_placeholder_replaced(self, tmp_path: pathlib.Path) -> None:
        """Empty CDATA <![CDATA[]]> is semantically equivalent to an empty element.
        xmltodict's expat parser raises no character event for empty CDATA, so the
        value is None — identical to <item/> or <item></item>.  The old '// hack'
        that forced the value to '//' has been removed."""
        xml_with_empty_cdata = (
            '<?xml version="1.0"?>'
            '<root><item><![CDATA[]]></item></root>'
        )
        f = tmp_path / 'cdata.xml'
        f.write_text(xml_with_empty_cdata, encoding='utf-8')
        result = dict_from_xml_file(str(f))
        assert isinstance(result, dict)
        assert result['root']['item'] is None

    def test_unicode_content_handled(self, tmp_path: pathlib.Path) -> None:
        xml_content = '<?xml version="1.0" encoding="UTF-8"?><root><val>héllo wörld</val></root>'
        f = tmp_path / 'unicode.xml'
        f.write_text(xml_content, encoding='utf-8')
        result = dict_from_xml_file(str(f))
        assert result is not None
        assert result['root']['val'] == 'héllo wörld'

    def test_nested_attributes_preserved(self, tmp_path: pathlib.Path) -> None:
        xml_content = '<root attr="top"><child sub="nested">value</child></root>'
        f = tmp_path / 'attrs.xml'
        f.write_text(xml_content, encoding='utf-8')
        result = dict_from_xml_file(str(f))
        assert result['root']['@attr'] == 'top'  # type: ignore
        assert result['root']['child']['@sub'] == 'nested'  # type: ignore
        assert result['root']['child']['#text'] == 'value'  # type: ignore


# ---------------------------------------------------------------------------
# is_valid_xml_file
# ---------------------------------------------------------------------------

class TestIsValidXmlFile:

    def test_fixture_file_is_valid(self, xml_fixture_path: pathlib.Path) -> None:
        assert is_valid_xml_file(str(xml_fixture_path)) is True

    def test_xml_declaration_detected(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / 'declared.xml'
        f.write_bytes(b'<?xml version="1.0"?><root/>')
        assert is_valid_xml_file(str(f)) is True

    def test_project_root_element_detected(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / 'project.xml'
        f.write_bytes(b'<project version="1"><item/></project>')
        assert is_valid_xml_file(str(f)) is True

    def test_eplan_root_element_detected(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / 'eplan.xml'
        f.write_bytes(b'<eplan><data/></eplan>')
        assert is_valid_xml_file(str(f)) is True

    def test_root_element_detected(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / 'root.xml'
        f.write_bytes(b'<root><child/></root>')
        assert is_valid_xml_file(str(f)) is True

    def test_document_element_detected(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / 'doc.xml'
        f.write_bytes(b'<document><section/></document>')
        assert is_valid_xml_file(str(f)) is True

    def test_generic_angle_bracket_content_valid(self, tmp_path: pathlib.Path) -> None:
        """A file with '<' and '>' that decodes as UTF-8 should be considered valid."""
        f = tmp_path / 'generic.xml'
        f.write_bytes(b'<custom><tag/></custom>')
        assert is_valid_xml_file(str(f)) is True

    def test_plain_text_file_is_not_valid(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / 'plain.txt'
        f.write_text('just some plain text with no xml tags', encoding='utf-8')
        assert is_valid_xml_file(str(f)) is False

    def test_binary_file_is_not_valid(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / 'binary.bin'
        f.write_bytes(bytes(range(256)))
        assert is_valid_xml_file(str(f)) is False

    def test_missing_file_raises_runtime_error(self, tmp_path: pathlib.Path) -> None:
        missing = str(tmp_path / 'nonexistent.xml')
        with pytest.raises(RuntimeError):
            is_valid_xml_file(missing)

    def test_case_insensitive_xml_declaration(self, tmp_path: pathlib.Path) -> None:
        """Detection must be case-insensitive (header is lowercased before matching)."""
        f = tmp_path / 'upper.xml'
        f.write_bytes(b'<?XML version="1.0"?><Root/>')
        assert is_valid_xml_file(str(f)) is True

    def test_large_file_only_reads_first_kb(self, tmp_path: pathlib.Path) -> None:
        """XML declaration at the start of a large file must still be detected."""
        content = b'<?xml version="1.0"?><root/>' + b'x' * (1024 * 100)
        f = tmp_path / 'large.xml'
        f.write_bytes(content)
        assert is_valid_xml_file(str(f)) is True


# ---------------------------------------------------------------------------
# xml_file_from_dict
# ---------------------------------------------------------------------------

class TestXmlFileFromDict:

    # --- output file existence and readability ---

    def test_creates_file(self, tmp_path: pathlib.Path) -> None:
        out = tmp_path / 'out.xml'
        xml_file_from_dict({'root': {'child': 'value'}}, str(out))
        assert out.exists()

    def test_output_is_valid_xml(self, tmp_path: pathlib.Path) -> None:
        out = tmp_path / 'out.xml'
        xml_file_from_dict({'root': {'child': 'value'}}, str(out))
        assert is_valid_xml_file(str(out)) is True

    def test_xml_declaration_present(self, tmp_path: pathlib.Path) -> None:
        out = tmp_path / 'out.xml'
        xml_file_from_dict({'root': None}, str(out))
        content = out.read_text(encoding='utf-8')
        assert content.startswith('<?xml')

    # --- extension handling ---

    def test_default_extension_xml(self, tmp_path: pathlib.Path) -> None:
        base = str(tmp_path / 'out')
        xml_file_from_dict({'root': None}, base)
        assert (tmp_path / 'out.xml').exists()

    def test_custom_extension_l5x(self, tmp_path: pathlib.Path) -> None:
        base = str(tmp_path / 'out')
        xml_file_from_dict({'root': None}, base, extension='.L5X')
        assert (tmp_path / 'out.L5X').exists()

    def test_extension_not_doubled(self, tmp_path: pathlib.Path) -> None:
        """save_file must not append the extension when it's already present."""
        out = str(tmp_path / 'out.xml')
        xml_file_from_dict({'root': None}, out)
        assert (tmp_path / 'out.xml').exists()
        assert not (tmp_path / 'out.xml.xml').exists()

    # --- round-trip (write → read back) ---

    def test_round_trip_simple(self, tmp_path: pathlib.Path) -> None:
        data = {'root': {'@attr': 'hello', 'child': 'world'}}
        out = tmp_path / 'rt.xml'
        xml_file_from_dict(data, str(out))
        result = dict_from_xml_file(str(out))
        assert result == data

    def test_round_trip_nested(self, tmp_path: pathlib.Path) -> None:
        data = {'root': {'level1': {'level2': {'val': '42'}}}}
        out = tmp_path / 'nested.xml'
        xml_file_from_dict(data, str(out))
        result = dict_from_xml_file(str(out))
        assert result == data

    def test_round_trip_fixture(
        self,
        xml_fixture_dict: dict,
        tmp_path: pathlib.Path,
    ) -> None:
        """Write the real L5X fixture dict back to disk and verify the structure
        is preserved when re-read."""
        out = tmp_path / 'fixture_rt.xml'
        xml_file_from_dict(xml_fixture_dict, str(out))
        result = dict_from_xml_file(str(out))
        assert result is not None
        assert 'RSLogix5000Content' in result
        ctrl = result['RSLogix5000Content']['Controller']
        assert ctrl['@Name'] == 'Base'

    # --- CDATA wrapping ---

    def test_no_cdata_by_default(self, tmp_path: pathlib.Path) -> None:
        out = tmp_path / 'no_cdata.xml'
        xml_file_from_dict({'root': {'Text': 'NOP();'}}, str(out))
        content = out.read_text(encoding='utf-8')
        assert '<![CDATA[' not in content

    def test_cdata_wraps_specified_element(self, tmp_path: pathlib.Path) -> None:
        out = tmp_path / 'cdata.xml'
        xml_file_from_dict(
            {'root': {'Text': 'NOP();'}},
            str(out),
            keep_cdata_sections=['Text'],
        )
        content = out.read_text(encoding='utf-8')
        assert '<![CDATA[NOP();]]>' in content

    def test_cdata_only_wraps_listed_elements(self, tmp_path: pathlib.Path) -> None:
        """Elements NOT in keep_cdata_sections must not get CDATA."""
        out = tmp_path / 'mixed.xml'
        xml_file_from_dict(
            {'root': {'Text': 'NOP();', 'Name': 'MyTag'}},
            str(out),
            keep_cdata_sections=['Text'],
        )
        content = out.read_text(encoding='utf-8')
        assert '<![CDATA[NOP();]]>' in content
        assert '<![CDATA[MyTag]]>' not in content

    def test_cdata_wraps_multiple_elements(self, tmp_path: pathlib.Path) -> None:
        out = tmp_path / 'multi_cdata.xml'
        xml_file_from_dict(
            {'root': {'Text': 'XIC(A)OTE(B);', 'Comment': 'My comment'}},
            str(out),
            keep_cdata_sections=['Text', 'Comment'],
        )
        content = out.read_text(encoding='utf-8')
        assert '<![CDATA[XIC(A)OTE(B);]]>' in content
        assert '<![CDATA[My comment]]>' in content

    def test_cdata_preserves_special_chars_unescaped(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Special XML characters inside CDATA must not be entity-escaped."""
        out = tmp_path / 'special.xml'
        xml_file_from_dict(
            {'root': {'Text': 'a < b && c > d'}},
            str(out),
            keep_cdata_sections=['Text'],
        )
        content = out.read_text(encoding='utf-8')
        assert '<![CDATA[a < b && c > d]]>' in content
        assert '&lt;' not in content
        assert '&amp;' not in content

    def test_cdata_none_value_not_wrapped(
        self, tmp_path: pathlib.Path
    ) -> None:
        """A None element value in a CDATA-listed tag must NOT inject <![CDATA[]]>.
        Mixed-content elements (e.g. Data Format='Message') have None text AND
        child elements; adding empty CDATA before the children causes Studio 5000
        to reject the file with 'Element value not expected for this element type.'"""
        out = tmp_path / 'none_cdata.xml'
        xml_file_from_dict(
            {'root': {'Text': None}},
            str(out),
            keep_cdata_sections=['Text'],
        )
        content = out.read_text(encoding='utf-8')
        assert '<![CDATA[' not in content

    def test_cdata_round_trip_with_fixture(
        self,
        xml_fixture_dict: dict,
        tmp_path: pathlib.Path,
    ) -> None:
        """Rung Text content must survive a write→read cycle with CDATA enabled."""
        out = tmp_path / 'cdata_rt.xml'
        xml_file_from_dict(
            xml_fixture_dict,
            str(out),
            keep_cdata_sections=['Text'],
        )
        result = dict_from_xml_file(str(out))
        assert result is not None
        ctrl = result['RSLogix5000Content']['Controller']
        programs = ctrl['Programs']['Program']
        standard = next(p for p in programs if p['@Name'] == 'StandardProgram')
        rung_text = standard['Routines']['Routine']['RLLContent']['Rung']['Text']
        assert 'NOP' in rung_text
