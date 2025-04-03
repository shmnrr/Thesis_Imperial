import re
import os
import sys

def auto_number_markdown_references(input_filepath, output_filepath=None):
    """
    Reads a Markdown file, finds list items formatted as potential references
    (e.g., "- [Text](link)"), numbers them sequentially, adds anchor IDs,
    and writes the result to an output file (or overwrites the input if no output is specified).

    Handles existing numbering like "[123] " by removing it before re-numbering.
    Also adds <a id="ref-X"></a> anchor tags to each reference for internal linking.
    Also updates citation references to these items throughout the document to use #ref-X format.
    """
    if output_filepath is None:
        output_filepath = input_filepath # Overwrite the original file

    # Regex to find list items (starting with '-' or '*') followed by a space,
    # optionally followed by an anchor tag and existing number "[digits] ",
    # then followed by the actual markdown link "[...](...)" or similar content.
    item_pattern = re.compile(r"^(\s*[-*]\s+)(?:<a id=\"ref-(\d+)\"></a>)?(?:\[(\d+)\]\s+)?(.*\[.+?\].*)$", re.IGNORECASE)

    # Simpler pattern just to identify potential list items to process
    potential_item_start = re.compile(r"^\s*[-*]\s+")

    # Read in the entire file
    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()
    except FileNotFoundError:
        print(f"Error: Input file '{input_filepath}' not found.")
        return 0
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return 0

    # First pass - identify all reference items for continuous numbering
    reference_ids = {}  # Maps existing ref-X IDs to new sequential numbers
    counter = 0
    
    # Collect all existing reference items and build mapping
    for i, line in enumerate(lines):
        if potential_item_start.match(line.lstrip()):
            match = item_pattern.match(line)
            if match and "<a id=\"ref-" in line and "[" in line and "]" in line and "(" in line and ")" in line:
                # This is a reference item with an anchor tag
                existing_id = match.group(2)  # Get the ID from anchor tag
                if existing_id:
                    counter += 1
                    reference_ids[existing_id] = counter

    # If no references were found, we'll need to start numbering from 1
    if counter == 0:
        counter = 1
    else:
        # Reset counter for second pass
        counter = 0
    
    # Second pass - renumber references and update content
    numbered_lines = []
    old_to_new_numbers = {}  # Maps old visible reference numbers to new ones
    
    for line in lines:
        # Check if the line looks like a list item
        if potential_item_start.match(line.lstrip()):
            match = item_pattern.match(line)
            if match and (match.group(4) is not None and "[" in match.group(4) and "]" in match.group(4)):
                # This looks like a reference item
                leading_whitespace_and_marker = match.group(1)
                existing_anchor_id = match.group(2)  # Get existing anchor ID number
                old_visible_number = match.group(3)  # Get the visible number
                content = match.group(4)
                
                counter += 1
                
                # Save mapping from old visible number to new number for citations
                if old_visible_number:
                    old_to_new_numbers[old_visible_number] = counter
                
                # Also map the anchor ID to the new number
                if existing_anchor_id:
                    old_to_new_numbers[existing_anchor_id] = counter
                
                # Prepend the new number and add an anchor tag for internal linking
                new_line = f"{leading_whitespace_and_marker}<a id=\"ref-{counter}\"></a>[{counter}] {content.lstrip()}\n"
                numbered_lines.append(new_line)
            else:
                # It's a list item but not a reference format we want to number
                numbered_lines.append(line)
        else:
            # Not a list item we want to number, keep it as is
            numbered_lines.append(line)

    # Third pass - update citations referencing the old numbers
    # Various pattern forms to find citations
    # Pattern for [44](#ref-44) format
    citation_pattern1 = re.compile(r'\[(\d+)\]\(#ref-(\d+)\)')
    # Pattern for [44](ref-44) format (missing the hash symbol)
    citation_pattern2 = re.compile(r'\[(\d+)\]\(ref-(\d+)\)')
    
    for i, line in enumerate(numbered_lines):
        # Skip lines that are the reference definitions themselves (already handled)
        if potential_item_start.match(line.lstrip()) and "<a id=\"ref-" in line:
            continue
        
        # Replace citations with the updated numbers (for the #ref format)
        def replace_citation1(match):
            old_num = match.group(1)
            ref_num = match.group(2)
            
            # Check if we have this number in our mapping
            if old_num in old_to_new_numbers:
                new_num = old_to_new_numbers[old_num]
                return f"[{new_num}](#ref-{new_num})"
            elif ref_num in old_to_new_numbers:
                new_num = old_to_new_numbers[ref_num]
                return f"[{new_num}](#ref-{new_num})"
            
            return match.group(0)  # Keep unchanged if not found in mapping
        
        # Replace citations with the updated numbers (for the ref format without #)
        def replace_citation2(match):
            old_num = match.group(1)
            ref_num = match.group(2)
            
            # Check if we have this number in our mapping
            if old_num in old_to_new_numbers:
                new_num = old_to_new_numbers[old_num]
                return f"[{new_num}](#ref-{new_num})"
            elif ref_num in old_to_new_numbers:
                new_num = old_to_new_numbers[ref_num]
                return f"[{new_num}](#ref-{new_num})"
            
            return match.group(0)  # Keep unchanged if not found in mapping
        
        # Apply both patterns
        numbered_lines[i] = re.sub(citation_pattern1, replace_citation1, numbered_lines[i])
        numbered_lines[i] = re.sub(citation_pattern2, replace_citation2, numbered_lines[i])

    # Write the modified content
    try:
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            outfile.writelines(numbered_lines)

        print(f"Successfully processed '{input_filepath}' and saved to '{output_filepath}'. Found {counter} reference items.")
        print(f"Added <a id=\"ref-X\"></a> anchor tags to each reference item for internal linking.")
        if old_to_new_numbers:
            print(f"Updated reference citations throughout the document to use #ref-X format.")
        return counter
    except Exception as e:
        print(f"An error occurred while writing the file: {e}")
        return 0

# Execute the function when the script is run directly
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Get the input file from command line arguments
        input_file = sys.argv[1]
        
        # Check if output file is specified as second argument
        output_file = None
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
            
        # Run the function
        auto_number_markdown_references(input_file, output_file)
    else:
        print("Usage: python number_refs.py input_file.md [output_file.md]")
        print("If output_file is not specified, the input file will be overwritten.")
        print("This script will add sequential numbering to reference-style list items,")
        print("add <a id=\"ref-X\"></a> anchor tags for internal linking,")
        print("and update any citations to these references throughout the document.")
        