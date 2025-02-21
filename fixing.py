import json

def split_definitions(data):
    """
    Split entries with multiple definitions into separate entries,
    each containing a single definition.
    """
    new_data = []
    
    for entry in data:
        word = entry[0]
        definitions = entry[5]
        
        # If there's only one definition, keep the entry as is
        if len(definitions) == 1:
            new_data.append(entry)
            continue
            
        # Create a new entry for each definition
        for definition in definitions:
            # Create a copy of the original entry
            new_entry = list(entry)
            # Replace definitions list with a single definition
            new_entry[5] = [definition]
            new_data.append(new_entry)
            
    return new_data

def process_file(input_file, output_file):
    """
    Process the input JSON file and write the transformed data to output file.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Transform the data
        transformed_data = split_definitions(data)
        
        # Write the transformed data to output file as a proper JSON array
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write opening bracket
            f.write('[\n')
            
            for i, entry in enumerate(transformed_data):
                # Convert entry to JSON string without pretty printing
                entry_json = json.dumps(entry, ensure_ascii=False)
                
                # Add comma for all entries except the last one
                if i < len(transformed_data) - 1:
                    f.write(f"  {entry_json},\n")
                else:
                    f.write(f"  {entry_json}\n")
            
            # Write closing bracket
            f.write(']')
        
        print(f"Successfully processed {input_file}")
        print(f"Original entries: {len(data)}")
        print(f"New entries: {len(transformed_data)}")
        
    except FileNotFoundError:
        print(f"Error: Could not find file {input_file}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {input_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    input_file = "MENSAH_FR_FR_Final\\term_bank_2.json"
    output_file = "term_bank_2.json"
    process_file(input_file, output_file)