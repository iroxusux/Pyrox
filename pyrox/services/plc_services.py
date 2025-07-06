""" plc_services
    Create and manage PLC specific l5x (xml) modules/services, etc.
    """
from __future__ import annotations


import os

from typing import Optional

from pyrox.models.gui import TaskFrame, PyroxGuiObject
import xmltodict
import lxml.etree
from xml.sax.saxutils import unescape
import xml.etree.ElementTree as ET


from .file import save_file


KEEP_CDATA_SECTION = [
    'AdditionalHelpText',
    'Comment',
    'Data',
    'DefaultData',
    'Description',
    'Line',
    'RevisionNote',
    'Text',
]


def cdata(s):
    """get cdata of string
    """
    if isinstance(s, str):
        return '<![CDATA[' + s + ']]>'


def l5x_dict_from_file(file_location: str) -> Optional[dict]:
    """get a controller dictionary from a provided .l5x file location

    Args:
        file_location (str): file location (must end in .l5x)

    Raises:
        ValueError: if provided file location is not .L5X

    Returns:
        dict: controller
    """
    if not file_location.endswith('.L5X'):
        raise ValueError('can only parse .L5X files!')

    if not os.path.exists(file_location):
        raise FileNotFoundError

    # use lxml and parse the .l5x xml into a dictionary
    try:
        parser = lxml.etree.XMLParser(strip_cdata=False)
        tree = lxml.etree.parse(file_location, parser)
        root = tree.getroot()
        xml_str = lxml.etree.tostring(root, encoding='utf-8').decode("utf-8")
    except FileNotFoundError:
        print(f"Error: File not found: {file_location}")
        return None
    except ET.ParseError:
        print(f"Error: Invalid XML format in {file_location}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    if not xml_str:
        return None

    # update c_data sections to create comments from all comment data
    try:
        xml_str = xml_str.replace("<![CDATA[]]>", "<![CDATA[//]]>")
        return xmltodict.parse(xml_str)
    except KeyError:
        return None


def dict_to_xml_file(controller: dict,
                     file_location: str) -> None:
    """save a dictionary "xml" controller back to .L5X

    Args:
        controller (dict): dictionary of parsed xml controller
        file_location (str): location to save controller .l5x to
    """
    save_file(file_location,
              '.L5X',
              'w',
              str(unescape(xmltodict.unparse(controller,
                                             preprocessor=preprocessor,
                                             pretty=True))))


def get_rung_text(rung):
    """Extract readable text from a rung if available"""
    text_element = rung.find("./Text")
    if text_element is not None and text_element.text:
        return text_element.text.strip()
    else:
        comment_element = rung.find("./Comment")
        if comment_element is not None and comment_element.text:
            return comment_element.text.strip()
    return "No description available"


def get_xml_string_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")

    try:
        parser = lxml.etree.XMLParser(strip_cdata=False)
        tree = lxml.etree.parse(file_path, parser)
        root = tree.getroot()
        return lxml.etree.tostring(root, encoding='utf-8').decode("utf-8")
    except (lxml.etree.ParseError, TypeError) as e:
        print(f"Error parsing XML file: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def preprocessor(key, value):
    '''Unneccessary if you've manually wrapped the values. For example,

    xmltodict.unparse({
        'node1': {'node2': '<![CDATA[test]]>', 'node3': 'test'}
    })
    '''

    if key in KEEP_CDATA_SECTION:
        if isinstance(value, dict) and '#text' in value:
            value['#text'] = cdata(value['#text'])
        elif isinstance(value, list):
            for v in value:
                preprocessor(key, v)
        elif isinstance(value, str):
            value = cdata(value)
    return key, value


def edit_plcobject_in_taskframe(parent,
                                plc_object,
                                resolver_method=None):
    """
    Create a TaskFrame with a GUI to edit all GUI properties of a PlcObject.
    Accepting changes updates the original object; canceling discards changes.

    .. ------------------------------------------------

    Args
    ------------
        parent (tk.Tk or tk.Frame): Parent widget for the TaskFrame.
        plc_object (PlcObject): The PLC object to edit.
        resolver_method (callable, optional): A method to resolve the GUI object from the PLC object.
    """
    import tkinter as tk
    from tkinter import messagebox
    from tkinter import ttk

    gui_object: PyroxGuiObject = resolver_method(plc_object)
    if not gui_object:
        messagebox.showerror("Error", "Invalid PLC object provided.")
        return None

    # Get editable property names from PlcObject
    prop_names = gui_object.gui_interface_attributes()
    # Prepare a dict to hold StringVars for each property
    prop_vars = {}

    # Create the TaskFrame
    frame = TaskFrame(parent, name=f"Edit {getattr(plc_object, 'name', plc_object.__class__.__name__)}")

    # Build the form inside the content_frame
    content = frame.content_frame
    for idx, prop in enumerate(prop_names):
        prop, prop_disp_name, prop_disp_type, editable = prop[0], prop[1], prop[2], prop[3] if isinstance(
            prop, tuple) else (prop, prop, tk.Label, False)

        if prop_disp_type is tk.Label:
            tk.Label(content, text=prop_disp_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
            value = getattr(plc_object, prop, "")
            var = tk.StringVar(value=str(value) if value is not None else "")
            entry = tk.Entry(content, textvariable=var, width=40)
            entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=2)
            entry.config(state='normal' if editable else 'disabled')
            if editable:
                prop_vars[prop] = var

        elif prop_disp_type is tk.Text:
            tk.Label(content, text=prop_disp_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
            value = getattr(plc_object, prop, "")
            var = tk.StringVar(value=str(value) if value is not None else "")
            entry = tk.Text(content, width=40, height=5)
            entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=2)
            entry.insert(tk.END, var.get())
            entry.config(state='normal' if editable else 'disabled')
            if editable:
                prop_vars[prop] = var

        elif prop_disp_type is ttk.Entry:
            tk.Label(content, text=prop_disp_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
            value = getattr(plc_object, prop, "")
            var = tk.StringVar(value=str(value) if value is not None else "")
            entry = ttk.Entry(content, textvariable=var, width=40)
            entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=2)
            entry.config(state='normal' if editable else 'disabled')
            if editable:
                prop_vars[prop] = var

        elif prop_disp_type is tk.Checkbutton:
            tk.Label(content, text=prop_disp_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
            value = getattr(plc_object, prop, False)
            var = tk.BooleanVar(value=value)
            entry = tk.Checkbutton(content, variable=var)
            entry.grid(row=idx, column=1, sticky='w', padx=5, pady=2)
            entry.config(state='normal' if editable else 'disabled')
            if editable:
                prop_vars[prop] = var

        elif prop_disp_type is ttk.Combobox:
            tk.Label(content, text=prop_disp_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
            value = getattr(plc_object, prop, "")
            var = tk.StringVar(value=str(value) if value is not None else "")
            entry = ttk.Combobox(content, textvariable=var, width=40)
            entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=2)
            entry['values'] = gui_object.get_property_choices(prop)
            entry.config(state='normal' if editable else 'disabled')
            if editable:
                prop_vars[prop] = var

    # Accept and Cancel button handlers
    def on_accept():
        for prop, var in prop_vars.items():
            # Try to set the property if it has a setter
            try:
                setattr(plc_object, prop, var.get())
            except Exception as e:
                messagebox.showerror("Error", f"Could not set {prop}: {e}")
        frame.destroy()

    def on_cancel():
        frame.destroy()

    # Add buttons
    btn_frame = tk.Frame(content)
    btn_frame.grid(row=len(prop_names), column=0, columnspan=2, pady=10)
    tk.Button(btn_frame, text="Accept", command=on_accept, width=10).pack(side='left', padx=5)
    tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side='left', padx=5)

    return frame
