"""
Quick EPLAN Data Inspector - Run this in your Python Debug Console

Copy and paste this into your debug console, then call:
inspect_project_data(project)  # where 'project' is your watch variable
"""

def inspect_project_data(data, max_depth=3, current_depth=0):
    """Quick inspection of project data structure."""
    if current_depth > max_depth:
        return f"... (depth limit reached)"
    
    if isinstance(data, dict):
        result = {}
        for key, value in list(data.items())[:10]:  # First 10 keys
            if key.startswith(('@', 'P', 'O', 'A', 'S')):
                if isinstance(value, (dict, list)) and current_depth < max_depth:
                    result[key] = inspect_project_data(value, max_depth, current_depth + 1)
                else:
                    result[key] = f"{type(value).__name__}: {str(value)[:50]}..."
        if len(data) > 10:
            result['...'] = f"({len(data) - 10} more keys)"
        return result
    elif isinstance(data, list):
        if len(data) > 0:
            return [inspect_project_data(data[0], max_depth, current_depth + 1), f"... ({len(data)} items)"]
        return []
    else:
        return f"{type(data).__name__}: {str(data)[:100]}"

def find_unmapped_keys(data, prefix=""):
    """Find keys that might not be in meta.py"""
    import re
    from pyrox.models.eplan import meta
    
    # Get current keys
    current_keys = set()
    for attr in dir(meta):
        if attr.endswith('_KEY'):
            current_keys.add(getattr(meta, attr))
    
    unmapped = []
    
    def scan(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_path = f"{path}.{key}" if path else key
                
                # Check if key matches EPLAN patterns
                if re.match(r'^@?[APS]\d+|^O\d+|^S\d+x\d+', key):
                    if key not in current_keys:
                        unmapped.append((key, full_path, type(value).__name__))
                
                # Recurse
                if isinstance(value, (dict, list)) and len(path.split('.')) < 4:
                    scan(value, full_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:5]):  # First 5 items
                scan(item, f"{path}[{i}]")
    
    scan(data)
    return unmapped

# Usage examples:
# 1. Basic inspection: inspect_project_data(project)
# 2. Find unmapped keys: find_unmapped_keys(project)
# 3. Get key counts: len([k for k in project.keys() if k.startswith('@P')])