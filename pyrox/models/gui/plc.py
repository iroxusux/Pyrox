"""This file contains GUI components for PLC (Programmable Logic Controller) objects.
    """
from __future__ import annotations


import tkinter as tk
from tkinter import ttk
from typing import Self

from .frames import ObjectEditField
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
    TagEndpoint,
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

    def gui_interface_attributes(self) -> list[ObjectEditField]:
        """Get the attributes of the PLC object that should be displayed in the GUI.

        This method is meant to be overridden by subclasses to provide
        specific attributes that should be displayed in a GUI context.

        Returns:
        ----------
            :type:`list[ObjectEditField]`: A list of `ObjectEditField` instances
            representing the attributes of the PLC object that should be displayed
        """
        return [ObjectEditField(
            property_name='meta_data',
            display_name='Meta Data',
            display_type=tk.Label,
            editable=False
        )]


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
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Text, True),
            ObjectEditField('file_location', 'File Location', tk.Label, False),
            ObjectEditField('comm_path', 'Communication Path', tk.Label, True),
            ObjectEditField('major_revision', 'Major Revision', tk.Label, True),
            ObjectEditField('minor_revision', 'Minor Revision', tk.Label, True),
            ObjectEditField('modules', 'Modules', None, False),
            ObjectEditField('aois', 'AOIs', None, False),
            ObjectEditField('datatypes', 'Data Types', None, False),
            ObjectEditField('tags', 'Tags', None, False),
            ObjectEditField('programs', 'Programs', None, False),
            ObjectEditField('root_meta_data', 'Root Meta Data', None, False),

        ]


class AddOnInstructionGuiObject(PlcGuiObject):
    """A GUI representation of an AddOnInstruction object."""

    def __init__(self, aoi: AddOnInstruction = None, **kwargs):
        super().__init__(plc_object=aoi, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Label, True),
            ObjectEditField('revision', 'Revision', tk.Label, True),
            ObjectEditField('execute_prescan', 'Execute Prescan', tk.Checkbutton, True),
            ObjectEditField('execute_postscan', 'Execute Postscan', tk.Checkbutton, True),
            ObjectEditField('execute_enable_in_false', 'Execute Enable In False', tk.Checkbutton, True),
            ObjectEditField('created_date', 'Created Date', tk.Label, False),
            ObjectEditField('created_by', 'Created By', tk.Label, False),
            ObjectEditField('edited_date', 'Edited Date', tk.Label, False),
            ObjectEditField('edited_by', 'Edited By', tk.Label, False),
            ObjectEditField('software_revision', 'Software Revision', tk.Label, False),
            ObjectEditField('revision_note', 'Revision Note', tk.Text, True),
            ObjectEditField('parameters', 'Parameters', None, False),
            ObjectEditField('local_tags', 'Local Tags', None, False),
        ]


class DatatypeGuiObject(PlcGuiObject):
    """A GUI representation of a Datatype object."""

    def __init__(self, datatype: Datatype = None, **kwargs):
        super().__init__(plc_object=datatype, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Label, True),
            ObjectEditField('family', 'Family', ttk.Combobox, True),
            ObjectEditField('members', 'Members', None, False),
        ]


class ModuleGuiObject(PlcGuiObject):
    """A GUI representation of a Module object."""

    def __init__(self, module: Module = None, **kwargs):
        super().__init__(plc_object=module, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Label, True),
            ObjectEditField('catalog_number', 'Catalog Number', tk.Label, True),
            ObjectEditField('vendor', 'Vendor', tk.Label, True),
            ObjectEditField('product_type', 'Product Type', tk.Label, True),
            ObjectEditField('product_code', 'Product Code', tk.Label, True),
            ObjectEditField('major', 'Major', tk.Label, True),
            ObjectEditField('minor', 'Minor', tk.Label, True),
            ObjectEditField('parent_module', 'Parent Module', tk.Label, False),
            ObjectEditField('parent_mod_port_id', 'Parent Mod Port Id', tk.Label, False),
            ObjectEditField('inhibited', 'Inhibited', tk.Checkbutton, True),
            ObjectEditField('major_fault', 'Major Fault', tk.Checkbutton, True),
            ObjectEditField('ekey', 'EKey', tk.Label, False),
            ObjectEditField('ports', 'Ports', None, False),
            ObjectEditField('communications', 'Communications', None, False),
        ]


class ProgramGuiObject(PlcGuiObject):
    """A GUI representation of a Program object."""

    def __init__(self, program: Program = None, **kwargs):
        super().__init__(plc_object=program, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Label, True),
            ObjectEditField('disabled', 'Disabled', tk.Checkbutton, True),
            ObjectEditField('main_routine_name', 'Main Routine Name', tk.Label, True),
            ObjectEditField('test_edits', 'Test Edits', tk.Checkbutton, True),
            ObjectEditField('use_as_folder', 'Use As Folder', tk.Checkbutton, True),
            ObjectEditField('input_instructions', 'Input Instructions', None, False),
            ObjectEditField('output_instructions', 'Output Instructions', None, False),
            ObjectEditField('routines', 'Routines', None, False),
            ObjectEditField('tags', 'Tags', None, False),
        ]


class RoutineGuiObject(PlcGuiObject):
    """A GUI representation of a Routine object."""

    def __init__(self, routine: Routine = None, **kwargs):
        super().__init__(plc_object=routine, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Label, True),
            ObjectEditField('input_instructions', 'Input Instructions', None, False),
            ObjectEditField('output_instructions', 'Output Instructions', None, False),
            ObjectEditField('instructions', 'Instructions', None, False),
            ObjectEditField('program', 'Program', tk.Label, False),
            ObjectEditField('rungs', 'Rungs', None, False),
        ]


class RungGuiObject(PlcGuiObject):
    """A GUI representation of a Rung object."""

    def __init__(self, rung: Rung = None, **kwargs):
        super().__init__(plc_object=rung, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('number', 'Number', tk.Label, True),
            ObjectEditField('comment', 'Comment', tk.Label, True),
            ObjectEditField('text', 'Text', tk.Text, True),
            ObjectEditField('type', 'Type', tk.Label, True),
            ObjectEditField('instructions', 'Instructions', None, False),
            ObjectEditField('input_instructions', 'Input Instructions', None, False),
            ObjectEditField('output_instructions', 'Output Instructions', None, False),
        ]


class TagEndpointGuiObject(PlcGuiObject):
    """A GUI representation of a TagEndpoint object."""

    def __init__(self, tag_endpoint: TagEndpoint = None, **kwargs):
        super().__init__(plc_object=tag_endpoint, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
        ]


class TagGuiObject(PlcGuiObject):
    """A GUI representation of a Tag object."""

    def __init__(self, tag: Tag = None, **kwargs):
        super().__init__(plc_object=tag, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Label, True),
            ObjectEditField('alias_for', 'Alias For', tk.Label, True),
            ObjectEditField('class_', 'Class', tk.Label, True),
            ObjectEditField('constant', 'Constant', tk.Checkbutton, True),
            ObjectEditField('datatype', 'Data Type', tk.Label, True),
            ObjectEditField('endpoint_operands', 'Endpoint Operands', tk.Text, False),
            ObjectEditField('external_access', 'External Access', tk.Label, True),
            ObjectEditField('opc_ua_access', 'OPC UA Access', tk.Label, True),
            ObjectEditField('scope', 'Scope', tk.Label, True),
            ObjectEditField('tag_type', 'Tag Type', tk.Label, True),
            ObjectEditField('data', 'Data', None, False),
            ObjectEditField('decorated_data', 'Decorated Data', None, False),
            ObjectEditField('l5k_data', 'L5K Data', None, False),
            ObjectEditField('datavalue_members', 'Data Value Members', None, False),
        ]


class DataValueMemberGuiObject(PlcGuiObject):
    """A GUI representation of a DataValueMember object."""

    def __init__(self, datavalue_member: DataValueMember = None, **kwargs):
        super().__init__(plc_object=datavalue_member, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Label, True),
            ObjectEditField('dimension', 'Dimension', tk.Label, True),
            ObjectEditField('hidden', 'Hidden', tk.Checkbutton, True),
            ObjectEditField('parent', 'Parent', tk.Label, False),
        ]


class ProgramTagGuiObject(PlcGuiObject):
    """A GUI representation of a ProgramTag object."""

    def __init__(self, program_tag: ProgramTag = None, **kwargs):
        super().__init__(plc_object=program_tag, **kwargs)

    def gui_interface_attributes(self):
        return [
            ObjectEditField('name', 'Name', tk.Label, True),
            ObjectEditField('description', 'Description', tk.Label, True),
            ObjectEditField('program', 'Program', tk.Label, False),
        ]
