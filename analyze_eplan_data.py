#!/usr/bin/env python3
"""
EPLAN Project Data Analysis Script

This script analyzes live EPLAN project data to identify patterns and missing
key-value mappings for the meta.py file.

Usage:
1. Set your project data in the 'project_data' variable below
2. Run the script to get analysis results
3. Use results to enhance your meta.py mappings
"""

from collections import defaultdict, Counter
import re
from typing import Dict, Any, List, Tuple
from pyrox.models.eplan import meta


def analyze_eplan_project_data(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze EPLAN project data to identify patterns and missing mappings.
    
    Args:
        project_data: Dictionary containing EPLAN project data
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'key_patterns': defaultdict(list),
        'missing_keys': set(),
        'value_patterns': defaultdict(list),
        'key_statistics': Counter(),
        'recommendations': []
    }
    
    # Get all currently mapped keys
    current_keys = set()
    for attr_name in dir(meta):
        if attr_name.endswith('_KEY') and not attr_name.startswith('_'):
            key_value = getattr(meta, attr_name)
            current_keys.add(key_value)
    
    def analyze_recursive(data, path=""):
        """Recursively analyze nested dictionary data."""
        if isinstance(data, dict):
            for key, value in data.items():
                full_path = f"{path}.{key}" if path else key
                
                # Track key patterns
                analysis['key_statistics'][key] += 1
                
                # Check for EPLAN property key patterns
                if re.match(r'^@?[A-Z]?\d+', key):
                    analysis['key_patterns']['property_keys'].append((key, full_path, type(value).__name__))
                    if key not in current_keys:
                        analysis['missing_keys'].add(key)
                
                # Check for object keys
                if re.match(r'^O\d+', key):
                    analysis['key_patterns']['object_keys'].append((key, full_path, type(value).__name__))
                    if key not in current_keys:
                        analysis['missing_keys'].add(key)
                
                # Check for property keys
                if re.match(r'^P\d+', key):
                    analysis['key_patterns']['property_keys'].append((key, full_path, type(value).__name__))
                    if key not in current_keys:
                        analysis['missing_keys'].add(key)
                
                # Check for section keys
                if re.match(r'^S\d+x\d+', key):
                    analysis['key_patterns']['section_keys'].append((key, full_path, type(value).__name__))
                    if key not in current_keys:
                        analysis['missing_keys'].add(key)
                
                # Analyze values for patterns
                if isinstance(value, str):
                    # Look for epoch timestamps
                    if re.match(r'^\d{10}$', value):
                        analysis['value_patterns']['epoch_timestamps'].append((key, value, full_path))
                    
                    # Look for file paths
                    if '\\' in value or '/' in value or value.endswith(('.ema', '.epj', '.L5X')):
                        analysis['value_patterns']['file_paths'].append((key, value, full_path))
                    
                    # Look for IP addresses
                    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
                        analysis['value_patterns']['ip_addresses'].append((key, value, full_path))
                    
                    # Look for device designations
                    if re.match(r'^[A-Z]+\d+', value) and len(value) < 20:
                        analysis['value_patterns']['device_designations'].append((key, value, full_path))
                
                # Recurse into nested structures
                analyze_recursive(value, full_path)
                
        elif isinstance(data, list):
            for i, item in enumerate(data):
                analyze_recursive(item, f"{path}[{i}]")
    
    # Perform the analysis
    analyze_recursive(project_data)
    
    # Generate recommendations
    if analysis['missing_keys']:
        analysis['recommendations'].append(
            f"Found {len(analysis['missing_keys'])} unmapped keys that could be added to meta.py"
        )
    
    if analysis['value_patterns']['epoch_timestamps']:
        analysis['recommendations'].append(
            "Found epoch timestamp patterns - consider adding date/time conversion utilities"
        )
    
    if analysis['value_patterns']['file_paths']:
        analysis['recommendations'].append(
            "Found file path patterns - consider adding file reference utilities"
        )
    
    return analysis


def print_analysis_report(analysis: Dict[str, Any]) -> None:
    """Print a formatted analysis report."""
    print("=" * 60)
    print("EPLAN PROJECT DATA ANALYSIS REPORT")
    print("=" * 60)
    
    print(f"\n🔑 KEY STATISTICS:")
    print(f"Total unique keys found: {len(analysis['key_statistics'])}")
    print(f"Missing keys not in meta.py: {len(analysis['missing_keys'])}")
    
    print(f"\n📊 KEY PATTERNS:")
    for pattern_type, keys in analysis['key_patterns'].items():
        print(f"\n{pattern_type.upper()} ({len(keys)} found):")
        for key, path, value_type in keys[:10]:  # Show first 10
            print(f"  {key} -> {value_type} (at {path})")
        if len(keys) > 10:
            print(f"  ... and {len(keys) - 10} more")
    
    print(f"\n🔍 MISSING KEYS TO ADD TO META.PY:")
    if analysis['missing_keys']:
        sorted_missing = sorted(analysis['missing_keys'])
        for key in sorted_missing[:20]:  # Show first 20
            print(f"  {key}")
        if len(sorted_missing) > 20:
            print(f"  ... and {len(sorted_missing) - 20} more")
    else:
        print("  No missing keys found!")
    
    print(f"\n💡 VALUE PATTERNS:")
    for pattern_type, values in analysis['value_patterns'].items():
        if values:
            print(f"\n{pattern_type.upper()} ({len(values)} found):")
            for key, value, path in values[:5]:  # Show first 5
                print(f"  {key}: {value} (at {path})")
            if len(values) > 5:
                print(f"  ... and {len(values) - 5} more")
    
    print(f"\n📝 RECOMMENDATIONS:")
    for i, recommendation in enumerate(analysis['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    print("\n" + "=" * 60)


def generate_meta_py_additions(missing_keys: set) -> str:
    """Generate code for adding missing keys to meta.py."""
    if not missing_keys:
        return "# No missing keys to add!"
    
    code_lines = ["# -------------- Additional Missing Keys -----------------"]
    
    # Group keys by pattern
    a_keys = [k for k in missing_keys if k.startswith('@A') or k.startswith('A')]
    p_keys = [k for k in missing_keys if k.startswith('@P') or k.startswith('P')]
    o_keys = [k for k in missing_keys if k.startswith('O')]
    s_keys = [k for k in missing_keys if k.startswith('S')]
    
    for key_group, description in [
        (a_keys, "Attribute Keys"),
        (p_keys, "Property Keys"), 
        (o_keys, "Object Keys"),
        (s_keys, "Section Keys")
    ]:
        if key_group:
            code_lines.append(f"\n# {description}")
            for key in sorted(key_group):
                var_name = f"EPLAN_{key.replace('@', '').replace('x', '_').upper()}_KEY"
                code_lines.append(f"{var_name} = '{key}'")
    
    return "\n".join(code_lines)


if __name__ == "__main__":
    # REPLACE THIS WITH YOUR ACTUAL PROJECT DATA FROM THE WATCH TABLE
    # Example structure - replace with your real data:
    project_data = {
        # Paste your project dictionary here
        # Example:
        # '@P10009': 'Your Project Name',
        # 'O4': {...},
        # etc.
    }
    
    print("🔎 EPLAN Data Analysis Tool")
    print("=" * 40)
    
    if not project_data or project_data == {}:
        print("❌ No project data provided!")
        print("\nTo use this tool:")
        print("1. Copy your project dictionary from the VS Code watch table")
        print("2. Paste it into the 'project_data' variable in this script")
        print("3. Run the script again")
        print("\nExample:")
        print("project_data = {")
        print("    '@P10009': 'Your Project Name',") 
        print("    'O4': {'sheet_data': '...'},")
        print("    # ... rest of your data")
        print("}")
    else:
        print(f"📄 Analyzing project data with {len(project_data)} top-level keys...")
        
        # Perform analysis
        analysis = analyze_eplan_project_data(project_data)
        
        # Print report
        print_analysis_report(analysis)
        
        # Generate code suggestions
        if analysis['missing_keys']:
            print("\n🔧 SUGGESTED CODE ADDITIONS FOR META.PY:")
            print("-" * 50)
            code_additions = generate_meta_py_additions(analysis['missing_keys'])
            print(code_additions)
            
            # Also suggest dictionary mappings
            print("\n📚 SUGGESTED DICTIONARY MAPPINGS:")
            print("-" * 50)
            for key in sorted(analysis['missing_keys'])[:10]:
                clean_key = key.replace('@', '').replace('x', '_').upper()
                var_name = f"EPLAN_{clean_key}_KEY"
                readable_name = clean_key.replace('_', ' ').title()
                print(f"    {var_name}: '{readable_name}',")