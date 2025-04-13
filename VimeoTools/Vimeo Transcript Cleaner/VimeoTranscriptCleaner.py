import re
import os

def clean_vtt(filepath, words_to_remove):
    with open(filepath, 'r') as file:
        lines = file.readlines()

    # Filter out lines that are not dialogue
    dialogue_lines = [line.strip() for line in lines if re.match(r"^\d+$", line) is None and "-->" not in line and line.strip()]

    # Concatenate all dialogue lines into a single text block
    dialogue_text = " ".join(dialogue_lines)

    # Remove unwanted words
    for word in words_to_remove:
        pattern = rf"\b{word}\b"
        dialogue_text = re.sub(pattern, '', dialogue_text, flags=re.IGNORECASE)

    # Remove extra whitespace
    cleaned_text = re.sub(r'\s+', ' ', dialogue_text).strip()

    # Save cleaned text to a new file in the same directory with "_CLEANED" appended to the filename
    base, ext = os.path.splitext(filepath)
    new_filepath = f"{base}_CLEANED.txt"
    with open(new_filepath, 'w') as cleaned_file:
        cleaned_file.write(cleaned_text)
    
    print(f"Cleaned file saved as: {new_filepath}")

# Editable list of words to remove
words_to_remove = ["uhhh+", "um", "essentially", "uh"]

# Filepath input from user with raw string
filepath = r"C:/Users/yusef/Local Documents/GMNG/Honeybook/MemberProfiles/ya214 Introduction Call.vtt"
# Clean and save the result
clean_vtt(filepath, words_to_remove)
