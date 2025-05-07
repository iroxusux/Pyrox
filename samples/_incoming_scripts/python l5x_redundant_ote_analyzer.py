import sys
import xml.etree.ElementTree as ET
import os
from collections import defaultdict


def parse_l5x_file(file_path):
    """Parse the L5X file and return the XML root element"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        return root
    except ET.ParseError as e:
        print(f"Error parsing L5X file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)


def find_redundant_otes(root):
    """Find redundant OTE instructions in the L5X file"""
    # Dictionary to store OTE operands and their locations
    ote_operands = defaultdict(list)

    # Find all routines in the program
    routines = []

    # Look for Controller/Programs/Program/Routines/Routine
    for program in root.findall(".//Program"):
        program_name = program.get('Name', 'Unknown')
        for routine in program.findall(".//Routine"):
            routine_name = routine.get('Name', 'Unknown')
            routines.append((program_name, routine_name, routine))

    # Process each routine
    for program_name, routine_name, routine in routines:
        # Look for RLL (Ladder Logic) routines
        rung_elements = routine.findall(".//RLLContent/Rung")

        # Process each rung
        for rung_idx, rung in enumerate(rung_elements, 1):
            # Find OTE instructions
            ote_elements = rung.findall(".//OTE")

            # Process each OTE instruction
            for ote in ote_elements:
                # Get the operand (tag name)
                operand = ote.get('Operand', '')

                if operand:
                    # Store the location information
                    location = {
                        'program': program_name,
                        'routine': routine_name,
                        'rung': rung_idx,
                        'text': get_rung_text(rung)
                    }
                    ote_operands[operand].append(location)

    # Filter out operands that are used in only one OTE instruction
    redundant_otes = {operand: locations for operand, locations in ote_operands.items() if len(locations) > 1}

    return redundant_otes


def get_rung_text(rung):
    """Extract readable text from a rung if available"""
    text_element = rung.find("./Text")
    if text_element is not None and text_element.text:
        return text_element.text.strip()
    else:
        comment_element = rung.find("./Comment")
        if comment_element is not None and comment_element.text:
            return comment_element.text.strip()
    return "No description available"


def print_redundant_otes(redundant_otes):
    """Print the redundant OTEs information"""
    if not redundant_otes:
        print("No redundant OTEs found in the program.")
        return

    print(f"\nFound {len(redundant_otes)} redundant OTEs:\n")

    for operand, locations in redundant_otes.items():
        print(f"Operand: {operand}")
        print(f"Used in {len(locations)} different places:")

        for idx, location in enumerate(locations, 1):
            print(f"  {idx}. Program: {location['program']}, "
                  f"Routine: {location['routine']}, "
                  f"Rung: {location['rung']}")
            print(f"     Description: {location['text'][:100]}...")

        print("\n" + "-" * 80 + "\n")


def save_report_to_file(redundant_otes, input_file):
    """Save the redundant OTEs report to a file"""
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_filename}_redundant_otes_report.txt"

    with open(output_file, "w") as f:
        if not redundant_otes:
            f.write("No redundant OTEs found in the program.\n")
            return output_file

        f.write(f"Redundant OTEs Analysis Report for {input_file}\n")
        f.write(f"Found {len(redundant_otes)} redundant OTEs:\n\n")

        for operand, locations in redundant_otes.items():
            f.write(f"Operand: {operand}\n")
            f.write(f"Used in {len(locations)} different places:\n")

            for idx, location in enumerate(locations, 1):
                f.write(f"  {idx}. Program: {location['program']}, "
                        f"Routine: {location['routine']}, "
                        f"Rung: {location['rung']}\n")
                f.write(f"     Description: {location['text'][:100]}...\n")

            f.write("\n" + "-" * 80 + "\n\n")

    return output_file


def main():
    """Main function to run the script"""
    if len(sys.argv) != 2:
        print("Usage: python l5x_redundant_ote_analyzer.py path/to/your/file.L5X")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"Analyzing L5X file: {file_path}")

    # Parse the L5X file
    root = parse_l5x_file(file_path)

    # Find redundant OTEs
    redundant_otes = find_redundant_otes(root)

    # Print the results
    print_redundant_otes(redundant_otes)

    # Save the report to a file
    output_file = save_report_to_file(redundant_otes, file_path)
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()
