import json
import re
from collections import defaultdict

# Load and analyze
with open(r'C:\Users\brian\Github\Pyrox\artifacts\unknown_controller_eplan_project.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Current keys from meta.py (expanded list)
current_keys = {
    'P11', 'P49', 'O3', 'O4', 'O6', 'O14', 'O17', 'O30', 'O52', 'O76', 'O117', 'O211',
    'S212x5', 'S75x5', '@A22', '@A48', '@A82', '@A133', '@A511', '@A1101', '@A1102',
    '@A1408', '@A1410', '@A1413', '@A2196', '@P1002', '@P1009', '@P1100', '@P1200',
    '@P10001', '@P10002', '@P10003', '@P10004', '@P10009', '@P10010', '@P10011',
    '@P10012', '@P10013', '@P10015', '@P10016', '@P10017', '@P10020', '@P10021',
    '@P10022', '@P10023', '@P10027', '@P10032', '@P10035', '@P10043', '@P10045',
    '@P10046', '@P10069', '@P10160', '@P10180', '@P10184', '@P10185', '@P11011',
    '@P11012', '@P11013', '@P11015', '@P11016', '@P11020', '@P11021', '@P11022',
    '@P11023', '@P11033', '@P11056', '@P11059', '@P11063', '@P11066', '@P11067',
    '@P2200', '@P22001', '@P22002', '@P22003', '@P22004', '@P22005', '@P22006',
    '@P22007', '@P22901', '@P22902', '@P22980', '@P22981', '@P22982', '@P22983',
    'P20011', 'P20049', 'P20050', 'P20051', 'P20094', 'P20216', 'P20400', 'P20468', 'P31030',
    '@P22042', '@P22046', '@P22122', '@P22131', '@P22138'
}

missing_keys = set()
sample_values = {}
key_categories = defaultdict(list)

def extract_keys(obj, max_depth=8):
    if max_depth <= 0:
        return
        
    if isinstance(obj, dict):
        for key, value in obj.items():
            if re.match(r'^@[AP]\d+|^[APS]\d+|^O\d+|^S\d+x\d+', str(key)):
                if key not in current_keys:
                    missing_keys.add(key)
                    if key not in sample_values:
                        sample_values[key] = str(value)[:60] if isinstance(value, str) else str(type(value).__name__)
                    
                    # Categorize keys
                    if key.startswith('@A'):
                        key_categories['attribute_keys'].append(key)
                    elif key.startswith('@P'):
                        key_categories['property_keys'].append(key)
                    elif key.startswith('O'):
                        key_categories['object_keys'].append(key)
                    elif key.startswith('S') and 'x' in key:
                        key_categories['section_keys'].append(key)
                    elif key.startswith('P'):
                        key_categories['plain_property_keys'].append(key)
                    elif key.startswith('A'):
                        key_categories['plain_attribute_keys'].append(key)
            
            if isinstance(value, (dict, list)):
                extract_keys(value, max_depth - 1)
    
    elif isinstance(obj, list):
        for item in obj[:3]:  # Sample first 3 items
            extract_keys(item, max_depth - 1)

extract_keys(data)

print('🎯 DETAILED MISSING KEY ANALYSIS')
print('=' * 60)
print(f'Total missing keys: {len(missing_keys)}')

for category, keys in key_categories.items():
    if keys:
        print(f'\n📋 {category.upper().replace("_", " ")} ({len(keys)} keys):')
        sorted_keys = sorted(keys)
        for i, key in enumerate(sorted_keys[:15]):
            sample = sample_values.get(key, 'No sample')
            print(f'  {i+1:2d}. {key:<12} -> {sample}')
        if len(sorted_keys) > 15:
            print(f'      ... and {len(sorted_keys) - 15} more')

print(f'\n🔧 SUGGESTED META.PY ADDITIONS:')
print('=' * 40)

# Generate key definitions by category
for category, keys in [('Attribute Keys (@A)', key_categories['attribute_keys'][:10]), 
                       ('Property Keys (@P)', key_categories['property_keys'][:10]),
                       ('Object Keys (O)', key_categories['object_keys'][:5]),
                       ('Section Keys (S)', key_categories['section_keys'][:5])]:
    if keys:
        print(f'\n# {category}')
        for key in sorted(keys):
            var_name = f'EPLAN_{key.replace("@", "").replace("x", "_").upper()}_KEY'
            print(f'{var_name} = "{key}"')

print(f'\n📚 SUGGESTED DICTIONARY MAPPINGS:')
print('=' * 40)
for category, keys in key_categories.items():
    if keys and len(keys) > 0:
        print(f'\n    # {category.replace("_", " ").title()}')
        for key in sorted(keys)[:8]:
            var_name = f'EPLAN_{key.replace("@", "").replace("x", "_").upper()}_KEY'
            readable_name = key.replace('@', '').replace('x', ' ').replace('P', 'Property ').replace('A', 'Attribute ').title()
            print(f'    {var_name}: \'{readable_name}\',')