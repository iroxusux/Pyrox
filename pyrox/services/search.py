from typing import List
import fnmatch


def check_wildcard_patterns(
    items: List[str],
    patterns: List[str]
) -> bool:
    """Check if any item matches any wildcard pattern."""
    for item in items:
        for pattern in patterns:
            if fnmatch.fnmatch(item, pattern):
                return True
    return False


def find_duplicates(
    input_list,
    include_orig: bool = False
) -> List:
    seen = set()
    duplicates = []

    for item in input_list:
        if item in seen:
            if not include_orig:
                duplicates.append(item)
            else:
                duplicates.append((item, next((y for y in seen if y == item), None)))
        else:
            seen.add(item)

    return duplicates
