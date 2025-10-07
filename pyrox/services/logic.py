"""General logic services module
"""


def function_list_or_chain(functions):
    """Chains a list of functions together with OR logic

    Args:
        functions (list): List of functions to chain together

    Returns:
        bool: False if any function returns False, True if all return True
    """
    pass_status = True
    for func in functions:
        if not func():
            pass_status = False
    return pass_status
