import json

def extract_words_from_json(json_file, output_file):
    """
    Extracts single words from a JSON file and writes them to a text file as comma-separated values.
    Skips entries containing whitespace.
    
    Args:
        json_file (str): Path to the JSON file
        output_file (str): Path to the output text file
    """
    try:
        # Read and parse the JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract words (first element of each array), skip if contains whitespace
        words = []
        for entry in data:
            if isinstance(entry, list) and len(entry) >= 1:
                word = entry[0]
                if isinstance(word, str) and word and ' ' not in word:  # Check if word is single word
                    words.append(word)
        
        # Write words to text file as comma-separated values
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(','.join(words))
            
        print(f"Successfully wrote {len(words)} words to {output_file}")
        skipped = len(data) - len(words)
        if skipped > 0:
            print(f"Skipped {skipped} entries containing whitespace")
        
    except FileNotFoundError:
        print(f"Error: File {json_file} not found")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format")
    except Exception as e:
        print(f"Error: {str(e)}")

# Example usage
if __name__ == "__main__":
    json_file = "/home/deck/larousse_api/larousse_api/test.json"
    output_file = "words_test.txt"
    extract_words_from_json(json_file, output_file)