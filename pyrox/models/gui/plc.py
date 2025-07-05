"""This file contains GUI components for PLC (Programmable Logic Controller) objects.
    """
from __future__ import annotations


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
        """Get the attributes of the PLC object that should be displayed in the GUI."""
        return [('meta_data', 'Meta Data'),]


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
        """Get the attributes of the Controller object that should be displayed in the GUI."""
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('file_location', 'File Location'),
            ('comm_path', 'Communication Path'),
            ('major_revision', 'Major Revision'),
            ('minor_revision', 'Minor Revision'),
            ('modules', 'Modules'),
            ('aois', 'AOIs'),
            ('datatypes', 'Data Types'),
            ('tags', 'Tags'),
            ('programs', 'Programs'),
        ]


class AddOnInstructionGuiObject(PlcGuiObject):
    """A GUI representation of an AddOnInstruction object."""

    def __init__(self, aoi: AddOnInstruction = None, **kwargs):
        super().__init__(plc_object=aoi, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('revision', 'Revision'),
            ('execute_prescan', 'Execute Prescan'),
            ('execute_postscan', 'Execute Postscan'),
            ('execute_enable_in_false', 'Execute Enable In False'),
            ('created_date', 'Created Date'),
            ('created_by', 'Created By'),
            ('edited_date', 'Edited Date'),
            ('edited_by', 'Edited By'),
            ('software_revision', 'Software Revision'),
            ('revision_note', 'Revision Note'),
            ('parameters', 'Parameters'),
            ('local_tags', 'Local Tags'),
        ]


class DatatypeGuiObject(PlcGuiObject):
    """A GUI representation of a Datatype object."""

    def __init__(self, datatype: Datatype = None, **kwargs):
        super().__init__(plc_object=datatype, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('family', 'Family'),
            ('members', 'Members'),
        ]


class ModuleGuiObject(PlcGuiObject):
    """A GUI representation of a Module object."""

    def __init__(self, module: Module = None, **kwargs):
        super().__init__(plc_object=module, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('catalog_number', 'Catalog Number'),
            ('vendor', 'Vendor'),
            ('product_type', 'Product Type'),
            ('product_code', 'Product Code'),
            ('major', 'Major'),
            ('minor', 'Minor'),
            ('parent_module', 'Parent Module'),
            ('parent_mod_port_id', 'Parent Mod Port Id'),
            ('inhibited', 'Inhibited'),
            ('major_fault', 'Major Fault'),
            ('ekey', 'EKey'),
            ('ports', 'Ports'),
            ('communications', 'Communications'),
        ]


class ProgramGuiObject(PlcGuiObject):
    """A GUI representation of a Program object."""

    def __init__(self, program: Program = None, **kwargs):
        super().__init__(plc_object=program, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('disabled', 'Disabled'),
            ('main_routine_name', 'Main Routine Name'),
            ('test_edits', 'Test Edits'),
            ('use_as_folder', 'Use As Folder'),
            ('input_instructions', 'Input Instructions'),
            ('output_instructions', 'Output Instructions'),
            ('routines', 'Routines'),
            ('tags', 'Tags'),
        ]


class RoutineGuiObject(PlcGuiObject):
    """A GUI representation of a Routine object."""

    def __init__(self, routine: Routine = None, **kwargs):
        super().__init__(plc_object=routine, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('input_instructions', 'Input Instructions'),
            ('output_instructions', 'Output Instructions'),
            ('instructions', 'Instructions'),
            ('program', 'Program'),
            ('rungs', 'Rungs'),
        ]


class RungGuiObject(PlcGuiObject):
    """A GUI representation of a Rung object."""

    def __init__(self, rung: Rung = None, **kwargs):
        super().__init__(plc_object=rung, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('number', 'Number'),
            ('comment', 'Comment'),
            ('text', 'Text'),
            ('type', 'Type'),
            ('instructions', 'Instructions'),
            ('input_instructions', 'Input Instructions'),
            ('output_instructions', 'Output Instructions'),
        ]


class TagGuiObject(PlcGuiObject):
    """A GUI representation of a Tag object."""

    def __init__(self, tag: Tag = None, **kwargs):
        super().__init__(plc_object=tag, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('alias_for', 'Alias For'),
            ('class_', 'Class'),
            ('constant', 'Constant'),
            ('datatype', 'Data Type'),
            ('external_access', 'External Access'),
            ('opc_ua_access', 'OPC UA Access'),
            ('scope', 'Scope'),
            ('tag_type', 'Tag Type'),
            ('data', 'Data'),
            ('decorated_data', 'Decorated Data'),
            ('l5k_data', 'L5K Data'),
            ('datavalue_members', 'Data Value Members'),
        ]


class DataValueMemberGuiObject(PlcGuiObject):
    """A GUI representation of a DataValueMember object."""

    def __init__(self, datavalue_member: DataValueMember = None, **kwargs):
        super().__init__(plc_object=datavalue_member, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('dimension', 'Dimension'),
            ('hidden', 'Hidden'),
            ('parent', 'Parent'),
        ]


class ProgramTagGuiObject(PlcGuiObject):
    """A GUI representation of a ProgramTag object."""

    def __init__(self, program_tag: ProgramTag = None, **kwargs):
        super().__init__(plc_object=program_tag, **kwargs)

    def gui_interface_attributes(self):
        return [
            ('name', 'Name'),
            ('description', 'Description'),
            ('program', 'Program'),
        ]
