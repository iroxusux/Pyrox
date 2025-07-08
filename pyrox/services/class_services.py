""" class services module.
    """
import os
import importlib.util
import inspect
from typing import Optional


def find_and_instantiate_class(directory_path: str,
                               class_name: str,
                               as_subclass: Optional[bool] = False,
                               ignoring_classes: Optional[list[str]] = None,
                               parent_class: Optional[type] = None,
                               **kwargs):
    """.. description::
    Searches for a class in the specified directory and its subdirectories,
    instantiates it, and returns a list of instances.
    .. ---------------------------------------------------------
    .. arguments::
        directory_path :class:`str`
            The path to the directory where the class is located.
        class_name :class:`str`
            The name of the class to search for.
        as_subclass :class:`bool`, optional
            If True, the function will search for subclasses of the specified class.
        ignoring_classes :class:`list[str]`, optional
            A list of class names to ignore during the search.
        parent_class :class:`type`, optional
            If `as_subclass` is True, this is the parent class to check against.
    .. ---------------------------------------------------------
    .. returns::
        :class:`list`
            A list of instantiated objects of the specified class.
    """
    objects = []
    ignoring_classes = ignoring_classes or []

    for filename in os.listdir(directory_path):
        if filename == '__init__.py':
            continue

        if os.path.isdir(os.path.join(directory_path, filename)):
            sub_objects = find_and_instantiate_class(directory_path=os.path.join(directory_path, filename),
                                                     class_name=class_name,
                                                     as_subclass=as_subclass,
                                                     ignoring_classes=ignoring_classes,
                                                     parent_class=parent_class,
                                                     **kwargs)
            objects.extend(sub_objects)
            continue

        if filename.endswith(".py"):
            module_name = filename[:-3]  # Remove .py extension
            file_path = os.path.join(directory_path, filename)

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None:
                continue  # Skip if spec cannot be created

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            objs = inspect.getmembers(module, inspect.isclass)

            for name, obj in objs:

                if name in ignoring_classes:
                    continue

                if as_subclass and parent_class is not None:
                    if issubclass(obj, parent_class):
                        objects.append(obj(**kwargs))
                else:
                    if name == class_name:
                        objects.append(obj(**kwargs))
    return objects


def class_to_dict(obj):
    """
    Recursively converts a class instance and its nested class instances
    into a dictionary.
    """
    if not hasattr(obj, '__dict__'):
        # If the object does not have a __dict__ (e.g., a basic type like int, str, list),
        # return it directly. Handle lists/tuples recursively if they contain objects.
        if isinstance(obj, (list, tuple)):
            return [class_to_dict(item) for item in obj]
        return obj

    result = {}
    for key, value in obj.__dict__.items():
        if key.startswith('__'):  # Skip built-in attributes
            continue

        if hasattr(value, '__dict__'):
            # If the value is another class instance, recurse
            result[key] = class_to_dict(value)
        elif isinstance(value, (list, tuple)):
            # If the value is a list or tuple, iterate and recurse on its elements
            result[key] = [class_to_dict(item) for item in value]
        else:
            # Otherwise, add the value directly
            result[key] = value
    return result
