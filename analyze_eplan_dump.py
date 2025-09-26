#!/usr/bin/env python3
"""
EPLAN Project Key Analyzer
Analyzes the large EPLAN JSON dump to find patterns and missing key mappings
"""

import json
import re
from collections import Counter, defaultdict
from pyrox.models.eplan import meta

def analyze_eplan_keys():
    """Extract and analyze EPLAN keys from the project dump."""
    
    print("🔍 EPLAN Project Key Analysis")
    print("=" * 50)
    
    # Get currently mapped keys from meta.py
    current_keys = set()
    current_mappings = {}
    
    for attr_name in dir(meta):
        if attr_name.endswith('_KEY') and not attr_name.startswith('_'):
            key_value = getattr(meta, attr_name)
            current_keys.add(key_value)
            current_mappings[key_value] = attr_name
    
    print(f"📋 Currently mapped keys in meta.py: {len(current_keys)}")
    
    # Analyze the JSON dump
    key_counter = Counter()
    key_patterns = defaultdict(list)
    sample_values = {}
    missing_keys = set()
    
    def extract_keys(obj, path="", max_depth=10):
        """Recursively extract keys from nested structure."""
        if max_depth <= 0:
            return
            
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Count all keys
                key_counter[key] += 1
                
                # Check for EPLAN patterns
                if re.match(r'^@[AP]\d+|^[APS]\d+|^O\d+|^S\d+x\d+', str(key)):
                    key_patterns['eplan_keys'].append(key)
                    
                    # Store sample value
                    if key not in sample_values:
                        sample_values[key] = str(value)[:100] if isinstance(value, str) else str(type(value).__name__)
                    
                    # Check if missing from meta.py
                    if key not in current_keys:
                        missing_keys.add(key)
                
                # Look for readable property names that map to keys
                if isinstance(value, str) and key in ['Properties', 'Project Title', 'Higher Level Function', 'Mounting Location', 'Project Description']:
                    key_patterns['readable_names'].append((key, str(value)[:50]))
                
                # Recurse
                if isinstance(value, (dict, list)):
                    extract_keys(value, f"{path}.{key}", max_depth - 1)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:10]):  # Sample first 10 items
                extract_keys(item, f"{path}[{i}]", max_depth - 1)
    
    # Process the large JSON file in chunks
    print("📖 Reading large JSON file...")
    
    try:
        with open(r'C:\Users\brian\Github\Pyrox\artifacts\unknown_controller_eplan_project.json', 'r', encoding='utf-8') as f:
            # Try to load the entire JSON
            data = json.load(f)
            print(f"✅ Successfully loaded JSON with {len(str(data))} characters")
            
            # Extract keys
            print("🔍 Extracting EPLAN keys...")
            extract_keys(data)
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return
    except MemoryError:
        print("❌ File too large for memory. Using streaming approach...")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Analysis Results
    print("\n" + "=" * 60)
    print("📊 ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"\n🔑 KEY STATISTICS:")
    print(f"Total unique keys found: {len(key_counter)}")
    print(f"EPLAN-style keys found: {len(key_patterns['eplan_keys'])}")
    print(f"Missing keys (not in meta.py): {len(missing_keys)}")
    
    print(f"\n📈 MOST COMMON KEYS:")
    for key, count in key_counter.most_common(20):
        status = "✅ MAPPED" if key in current_keys else "❌ MISSING"
        print(f"  {key}: {count} occurrences {status}")
    
    print(f"\n🎯 MISSING KEYS TO ADD TO META.PY:")
    sorted_missing = sorted(missing_keys)
    for i, key in enumerate(sorted_missing[:30]):
        sample_val = sample_values.get(key, "No sample")
        print(f"  {i+1:2d}. {key:<15} -> {sample_val}")
    
    if len(sorted_missing) > 30:
        print(f"     ... and {len(sorted_missing) - 30} more missing keys")
    
    # Generate code suggestions
    print(f"\n🔧 SUGGESTED META.PY ADDITIONS:")
    print("=" * 40)
    
    # Group missing keys by pattern
    a_keys = [k for k in sorted_missing if k.startswith('@A') or (k.startswith('A') and k[1:].isdigit())]
    p_keys = [k for k in sorted_missing if k.startswith('@P') or (k.startswith('P') and k[1:].isdigit())]
    o_keys = [k for k in sorted_missing if k.startswith('O') and k[1:].isdigit()]
    s_keys = [k for k in sorted_missing if k.startswith('S') and 'x' in k]
    
    for key_group, description in [
        (a_keys[:10], "Attribute Keys (A-series)"),
        (p_keys[:10], "Property Keys (P-series)"), 
        (o_keys[:10], "Object Keys (O-series)"),
        (s_keys[:5], "Section Keys (S-series)")
    ]:
        if key_group:
            print(f"\n# {description}")
            for key in key_group:
                var_name = f"EPLAN_{key.replace('@', '').replace('x', '_').upper()}_KEY"
                print(f"{var_name} = '{key}'")
    
    # Dictionary mappings
    print(f"\n📚 SUGGESTED DICTIONARY MAPPINGS:")
    print("=" * 40)
    for key in sorted_missing[:15]:
        var_name = f"EPLAN_{key.replace('@', '').replace('x', '_').upper()}_KEY"
        readable_name = key.replace('@', '').replace('x', ' ').replace('P', 'Property ').replace('A', 'Attribute ').title()
        print(f"    {var_name}: '{readable_name}',")
    
    print(f"\n✨ ANALYSIS COMPLETE!")
    print(f"Found {len(missing_keys)} new keys that could enhance your EPLAN project disambiguation!")

if __name__ == "__main__":
    analyze_eplan_keys()