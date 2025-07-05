"""This file contains GUI components for PLC (Programmable Logic Controller) objects.
    """
from __future__ import annotations


import tkinter as tk
from tkinter import ttk
from typing import Self


from .pyroxguiobject import PyroxGuiObject
from ..plc import (
    PlcObject,
    Controller,
    AddOnInstruction,
    Datatype,
    Module,
    Program,
    Routine,
    Rung,
    Tag,
    DataValueMember,
    ProgramTag
)


class PlcGuiObject(PyroxGuiObject):
    """A GUI representation of a PLC object.

    This class extends the `PyroxGuiObject` to provide a specific representation 

    of PLC objects in the GUI. It can be used to display PLC properties and

    methods in a user-friendly manner."""

    def __init__(self,
                 plc_object: PlcObject = None,
                 **kwargs):
        super().__init__(plc_object,
                         **kwargs)

    @classmethod
    def from_data(cls,
                  data: PlcObject) -> Self:
        """Get a new instance of this class from data.

        This method is intended to be overridden by subclasses to provide a
        specific way to create an instance from data.

        Args:
            data (PlcObject): The PLC object to create the GUI representation for.
        """
        if isinstance(data, Controller):
            return ControllerGuiObject(controller=data)
        if isinstance(data, AddOnInstruction):
            return AddOnInstructionGuiObject(aoi=data)
        if isinstance(data, Datatype):
            return DatatypeGuiObject(datatype=data)
        if isinstance(data, Module):
            return ModuleGuiObject(module=data)
        if isinstance(data, Program):
            return ProgramGuiObject(program=data)
        if isinstance(data, Routine):
            return RoutineGuiObject(routine=data)
        if isinstance(data, Rung):
            return RungGuiObject(rung=data)
        if isinstance(data, Tag):
            return TagGuiObject(tag=data)
        if isinstance(data, DataValueMember):
            return DataValueMemberGuiObject(datavalue_member=data)
        if isinstance(data, ProgramTag):
            return ProgramTagGuiObject(program_tag=data)

        return cls(plc_object=data)

    def gui_interface_attributes(self) -> list[tuple[str, str]]:
        """Get the attributes of the PLC object that should be displayed in the GUI.

        This method is meant to be overridden by subclasses to provide
        specific attributes that should be displayed in a GUI context.

        Returns:
        ----------
            :type:`list[tuple[str, str, tk.Widget, bool]]`: A list of tuples where each tuple contains
            the attribute name, its display name, the widget type to use for display, and a boolean indicating if it is editable.
        """
        return [('meta_data', 'Meta Data', tk.Label, False),]


class ControllerGuiObject(PlcGuiObject):
    """A GUI representation of a PLC Controller object.

    This class extends the `PyroxGuiObject` to provide a specific representation

    of PLC Controller objects in the GUI. It can be used to display controller

    properties and methods in a user-friendly manner."""

    def __init__(self,
                 controller: Controller = None,
                 **kwargs):
        super().__init__(plc_object=controller,
                         **kwargs)

    def gui_interface_attributes(self) -> list[tuple[str, str]]:
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('file_location', 'File Location', tk.Label, False),
            ('comm_path', 'Communication Path', tk.Label, True),
            ('major_revision', 'Major Revision', tk.Label, True),
            ('minor_revision', 'Minor Revision', tk.Label, True),
            ('modules', 'Modules', None, False),
            ('aois', 'AOIs', None, False),
            ('datatypes', 'Data Types', None, False),
            ('tags', 'Tags', None, False),
            ('programs', 'Programs', None, False),
            ('root_meta_data', 'Root Meta Data', tk.Text, False),

        ]


class AddOnInstructionGuiObject(PlcGuiObject):
    """A GUI representation of an AddOnInstruction object."""

    def __init__(self, aoi: AddOnInstruction = None, **kwargs):
        super().__init__(plc_object=aoi, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('revision', 'Revision', tk.Label, True),
            ('execute_prescan', 'Execute Prescan', tk.Checkbutton, True),
            ('execute_postscan', 'Execute Postscan', tk.Checkbutton, True),
            ('execute_enable_in_false', 'Execute Enable In False', tk.Checkbutton, True),
            ('created_date', 'Created Date', tk.Label, False),
            ('created_by', 'Created By', tk.Label, False),
            ('edited_date', 'Edited Date', tk.Label, False),
            ('edited_by', 'Edited By', tk.Label, False),
            ('software_revision', 'Software Revision', tk.Label, False),
            ('revision_note', 'Revision Note', tk.Text, True),
            ('parameters', 'Parameters', None, False),
            ('local_tags', 'Local Tags', None, False),
        ]


class DatatypeGuiObject(PlcGuiObject):
    """A GUI representation of a Datatype object."""

    def __init__(self, datatype: Datatype = None, **kwargs):
        super().__init__(plc_object=datatype, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('family', 'Family', ttk.Combobox, True),
            ('members', 'Members', None, False),
        ]


class ModuleGuiObject(PlcGuiObject):
    """A GUI representation of a Module object."""

    def __init__(self, module: Module = None, **kwargs):
        super().__init__(plc_object=module, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('catalog_number', 'Catalog Number', tk.Label, True),
            ('vendor', 'Vendor', tk.Label, True),
            ('product_type', 'Product Type', tk.Label, True),
            ('product_code', 'Product Code', tk.Label, True),
            ('major', 'Major', tk.Label, True),
            ('minor', 'Minor', tk.Label, True),
            ('parent_module', 'Parent Module', tk.Label, False),
            ('parent_mod_port_id', 'Parent Mod Port Id', tk.Label, False),
            ('inhibited', 'Inhibited', tk.Checkbutton, True),
            ('major_fault', 'Major Fault', tk.Checkbutton, True),
            ('ekey', 'EKey', tk.Label, False),
            ('ports', 'Ports', None, False),
            ('communications', 'Communications', None, False),
        ]


class ProgramGuiObject(PlcGuiObject):
    """A GUI representation of a Program object."""

    def __init__(self, program: Program = None, **kwargs):
        super().__init__(plc_object=program, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('disabled', 'Disabled', tk.Checkbutton, True),
            ('main_routine_name', 'Main Routine Name', tk.Label, True),
            ('test_edits', 'Test Edits', tk.Checkbutton, True),
            ('use_as_folder', 'Use As Folder', tk.Checkbutton, True),
            ('input_instructions', 'Input Instructions', None, False),
            ('output_instructions', 'Output Instructions', None, False),
            ('routines', 'Routines', None, False),
            ('tags', 'Tags', None, False),
        ]


class RoutineGuiObject(PlcGuiObject):
    """A GUI representation of a Routine object."""

    def __init__(self, routine: Routine = None, **kwargs):
        super().__init__(plc_object=routine, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('input_instructions', 'Input Instructions', None, False),
            ('output_instructions', 'Output Instructions', None, False),
            ('instructions', 'Instructions', None, False),
            ('program', 'Program', tk.Label, False),
            ('rungs', 'Rungs', None, False),
        ]


class RungGuiObject(PlcGuiObject):
    """A GUI representation of a Rung object."""

    def __init__(self, rung: Rung = None, **kwargs):
        super().__init__(plc_object=rung, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('number', 'Number', tk.Label, True),
            ('comment', 'Comment', tk.Label, True),
            ('text', 'Text', tk.Text, True),
            ('type', 'Type', tk.Label, True),
            ('instructions', 'Instructions', None, False),
            ('input_instructions', 'Input Instructions', None, False),
            ('output_instructions', 'Output Instructions', None, False),
        ]


class TagGuiObject(PlcGuiObject):
    """A GUI representation of a Tag object."""

    def __init__(self, tag: Tag = None, **kwargs):
        super().__init__(plc_object=tag, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('alias_for', 'Alias For', tk.Label, True),
            ('class_', 'Class', tk.Label, True),
            ('constant', 'Constant', tk.Checkbutton, True),
            ('datatype', 'Data Type', tk.Label, True),
            ('external_access', 'External Access', tk.Label, True),
            ('opc_ua_access', 'OPC UA Access', tk.Label, True),
            ('scope', 'Scope', tk.Label, True),
            ('tag_type', 'Tag Type', tk.Label, True),
            ('data', 'Data', None, False),
            ('decorated_data', 'Decorated Data', None, False),
            ('l5k_data', 'L5K Data', None, False),
            ('datavalue_members', 'Data Value Members', None, False),
        ]


class DataValueMemberGuiObject(PlcGuiObject):
    """A GUI representation of a DataValueMember object."""

    def __init__(self, datavalue_member: DataValueMember = None, **kwargs):
        super().__init__(plc_object=datavalue_member, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('dimension', 'Dimension', tk.Label, True),
            ('hidden', 'Hidden', tk.Checkbutton, True),
            ('parent', 'Parent', tk.Label, False),
        ]


class ProgramTagGuiObject(PlcGuiObject):
    """A GUI representation of a ProgramTag object."""

    def __init__(self, program_tag: ProgramTag = None, **kwargs):
        super().__init__(plc_object=program_tag, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
            ('program', 'Program', tk.Label, False),
        ]
