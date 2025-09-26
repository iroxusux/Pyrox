# Copy and paste this into your debug console to explore project structure:

# Check project attributes
print("Project attributes:", [attr for attr in dir(project) if not attr.startswith("_")])

# Check main data containers
for attr in ["devices", "groups", "connections", "properties", "sheet_details", "bom_details"]:
    if hasattr(project, attr):
        data = getattr(project, attr)
        data_len = len(data) if hasattr(data, "__len__") else "unknown"
        print(f"{attr}: {type(data)} with {data_len} items")

# Look for EPLAN keys in different locations
locations_to_check = [
    ("project.__dict__", project.__dict__),
    ("project.properties", getattr(project, "properties", {})), 
    ("project.meta_data", getattr(project, "meta_data", {})),
    ("project.devices", getattr(project, "devices", [])),
]

for name, data in locations_to_check:
    if isinstance(data, dict):
        all_keys = list(data.keys())
        eplan_keys = [k for k in all_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
        print(f"{name}: {len(all_keys)} total keys, {len(eplan_keys)} EPLAN-style keys")
        if eplan_keys:
            print(f"  Sample EPLAN keys: {eplan_keys[:10]}")
    elif isinstance(data, list) and len(data) > 0:
        print(f"{name}: List with {len(data)} items")
        if hasattr(data[0], '__dict__'):
            sample_keys = list(data[0].__dict__.keys())
            eplan_keys = [k for k in sample_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
            print(f"  First item keys: {sample_keys}")
            if eplan_keys:
                print(f"  EPLAN-style keys in items: {eplan_keys}")

# Check if devices contain data dictionaries
if hasattr(project, 'devices') and len(project.devices) > 0:
    print("\nChecking device data structure:")
    first_device = project.devices[0]
    print(f"First device type: {type(first_device)}")
    print(f"First device attributes: {[attr for attr in dir(first_device) if not attr.startswith('_')]}")
    
    if hasattr(first_device, 'data'):
        device_data = first_device.data
        if isinstance(device_data, dict):
            all_keys = list(device_data.keys())
            eplan_keys = [k for k in all_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
            print(f"Device data: {len(all_keys)} total keys, {len(eplan_keys)} EPLAN-style keys")
            if eplan_keys:
                print(f"  Sample device EPLAN keys: {eplan_keys[:15]}")