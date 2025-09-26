# Copy and paste this into your debug console to find EPLAN keys in the data:

print("=== ANALYZING SHEET DETAILS ===")
if len(project.sheet_details) > 0:
    print(f"Sheet details: {len(project.sheet_details)} items")
    
    # Check first few sheet items
    for i in range(min(3, len(project.sheet_details))):
        sheet = project.sheet_details[i]
        print(f"\nSheet {i} type: {type(sheet)}")
        
        if isinstance(sheet, dict):
            all_keys = list(sheet.keys())
            eplan_keys = [k for k in all_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
            print(f"  Sheet {i} dict: {len(all_keys)} total keys, {len(eplan_keys)} EPLAN-style keys")
            if eplan_keys:
                print(f"    Sample EPLAN keys: {eplan_keys[:10]}")
        elif hasattr(sheet, '__dict__'):
            sheet_dict = sheet.__dict__
            all_keys = list(sheet_dict.keys())
            eplan_keys = [k for k in all_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
            print(f"  Sheet {i} object: {len(all_keys)} total keys, {len(eplan_keys)} EPLAN-style keys")
            if eplan_keys:
                print(f"    Sample EPLAN keys: {eplan_keys[:10]}")
            
            # Check if sheet has data attribute
            if hasattr(sheet, 'data') and isinstance(sheet.data, dict):
                data_keys = list(sheet.data.keys())  
                eplan_data_keys = [k for k in data_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
                print(f"    Sheet {i}.data: {len(data_keys)} total keys, {len(eplan_data_keys)} EPLAN-style keys")
                if eplan_data_keys:
                    print(f"      Sample data EPLAN keys: {eplan_data_keys[:15]}")

print("\n=== ANALYZING BOM DETAILS ===")
if len(project.bom_details) > 0:
    print(f"BOM details: {len(project.bom_details)} items")
    
    # Check first few BOM items
    for i in range(min(3, len(project.bom_details))):
        bom_item = project.bom_details[i]
        print(f"\nBOM {i} type: {type(bom_item)}")
        
        if isinstance(bom_item, dict):
            all_keys = list(bom_item.keys())
            eplan_keys = [k for k in all_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
            print(f"  BOM {i} dict: {len(all_keys)} total keys, {len(eplan_keys)} EPLAN-style keys")
            if eplan_keys:
                print(f"    Sample EPLAN keys: {eplan_keys[:10]}")
        elif hasattr(bom_item, '__dict__'):
            bom_dict = bom_item.__dict__
            all_keys = list(bom_dict.keys())
            eplan_keys = [k for k in all_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
            print(f"  BOM {i} object: {len(all_keys)} total keys, {len(eplan_keys)} EPLAN-style keys")
            if eplan_keys:
                print(f"    Sample EPLAN keys: {eplan_keys[:10]}")
                
            # Check if BOM item has data attribute
            if hasattr(bom_item, 'data') and isinstance(bom_item.data, dict):
                data_keys = list(bom_item.data.keys())
                eplan_data_keys = [k for k in data_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
                print(f"    BOM {i}.data: {len(data_keys)} total keys, {len(eplan_data_keys)} EPLAN-style keys")
                if eplan_data_keys:
                    print(f"      Sample data EPLAN keys: {eplan_data_keys[:15]}")

# Let's also check some other project attributes that might contain data
print("\n=== CHECKING OTHER PROJECT DATA ===")
for attr_name in ['project_data', 'project_properties', 'pxf_root']:
    if hasattr(project, attr_name):
        attr_data = getattr(project, attr_name)
        print(f"{attr_name}: {type(attr_data)}")
        
        if isinstance(attr_data, dict):
            all_keys = list(attr_data.keys())
            eplan_keys = [k for k in all_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
            print(f"  {attr_name}: {len(all_keys)} total keys, {len(eplan_keys)} EPLAN-style keys")
            if eplan_keys:
                print(f"    Sample EPLAN keys: {eplan_keys[:15]}")
        elif hasattr(attr_data, '__dict__'):
            attr_dict = attr_data.__dict__
            all_keys = list(attr_dict.keys())
            eplan_keys = [k for k in all_keys if str(k).startswith(("@P", "@A", "P", "A", "O", "S"))]
            print(f"  {attr_name} object: {len(all_keys)} total keys, {len(eplan_keys)} EPLAN-style keys")
            if eplan_keys:
                print(f"    Sample EPLAN keys: {eplan_keys[:15]}")