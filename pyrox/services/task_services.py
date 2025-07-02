import os
import importlib.util
import inspect


def find_and_instantiate_class(directory_path,
                               class_name,
                               as_subclass: bool = False,
                               ignoring_classes: list[str] = None,
                               parent_class: type = None,
                               **kwargs):
    """
    Checks Python files in a directory for a specific class and instantiates it.

    Args:
        directory_path (str): The path to the directory to search.
        class_name (str): The name of the class to find and instantiate.

    Returns:
        object: An instance of the found class, or None if the class is not found.
    """
    objects = []

    if not ignoring_classes:
        ignoring_classes = []

    for filename in os.listdir(directory_path):
        if filename == '__init__.py':
            continue

        if os.path.isdir(os.path.join(directory_path, filename)):
            # If it's a directory, recursively search in it
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
