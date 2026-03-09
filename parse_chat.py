import re
import pandas as pd
import sys
import os

def parse_whatsapp_chat(file_path):
    """
    Reads a raw WhatsApp .txt export and converts it into a structured Pandas DataFrame.
    WhatsApp exports text in a raw, loosely formatted way. To analyze it effectively for 
    metrics like heatmaps, we must extract the date, time, sender, and message into 
    separate, predictable columns.
    """
    
    # This Regular Expression (Regex) acts as a highly specific search filter to 
    # identify lines that indicate the start of a new message. It specifically 
    # looks for the standard WhatsApp format: "Date, Time - Sender: Message".
    #
    # Breakdown of the pattern:
    # Group 1: (\d{1,2}/\d{1,2}/\d{2,4}) captures the Date (e.g., 12/05/2023)
    # Group 2: (\d{1,2}:\d{2}\s?(?:[aApP][mM])?) captures the Time (e.g., 10:30 am)
    # Group 3: (.*?) non-greedily captures the Sender's name or phone number
    # Group 4: (.*) captures the actual Message text that follows the colon
    pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}\s?(?:[aApP][mM])?)\s-\s(.*?):\s(.*)$'
    
    # This list will accumulate all our cleaned, individual message rows
    parsed_data = [] 
    
    # We open the file with 'utf-8' encoding because WhatsApp chats heavily utilize 
    # emojis and special characters. UTF-8 ensures Python reads these correctly 
    # without throwing a UnicodeDecodeError.
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
    # Initialize variables to hold the current message's data as we iterate
    date, time, sender, message = None, None, None, ""
    
    for line in lines:
        match = re.match(pattern, line)
        
        if match:
            # When a regex match is found, it means we have hit a brand new message.
            # Before we start processing this new message, we must take the PREVIOUS 
            # message we were tracking and append it to our parsed_data list.
            if sender:
                parsed_data.append([date, time, sender, message.strip()])
            
            # Extract the new components from the regex groups and start tracking them
            date, time, sender, message_text = match.groups()
            message = message_text + " "
        else:
            # If the line does NOT match the Date/Time pattern, it means the user hit 
            # "Enter" while typing, creating a multi-line paragraph. We simply append 
            # this text to the current message string rather than creating a new row.
            if sender:
                message += line.strip() + " "
            
    # Once the loop finishes, the very last message in the chat is still sitting in 
    # our tracking variables. We append it manually here so it isn't left behind.
    if sender:
        parsed_data.append([date, time, sender, message.strip()])
        
    # We convert the Python list of lists into a Pandas DataFrame. DataFrames are 
    # powerful tabular structures that make it easy to filter, search, and export data.
    df = pd.DataFrame(parsed_data, columns=['Date', 'Time', 'Sender', 'Message'])
    
    # To generate time-based analytics later (like activity heatmaps), we need a 
    # single column that Pandas recognizes as a true "datetime" object, rather than 
    # just raw text. We combine the Date and Time columns to create this.
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], dayfirst=True, format='mixed', errors='coerce')
    
    return df

def rename_participants(df):
    """
    Identifies all unique senders in the chat and gives the user an interactive prompt 
    to rename them. Unsaved contacts often appear as raw phone numbers in the export. 
    Renaming them here ensures all future visualizations display clean, readable names.
    """
    
    # Extract an array of unique names and numbers from the Sender column
    unique_senders = df['Sender'].dropna().unique()
    
    print("\n" + "-"*50)
    print(f"👥 Found {len(unique_senders)} unique participants in this chat.")
    print("-"*50)
    
    # Give the user the choice to skip this process entirely if the names are already fine
    choice = input("Would you like to rename any participants (e.g., change phone numbers to names)? (y/n): ").strip().lower()
    
    if choice == 'y':
        # This dictionary will store the translation map, formatted as { 'Old Name' : 'New Name' }
        rename_mapping = {} 
        
        print("\nFor each participant, type the new name and press Enter.")
        print("If you want to keep the current name, just press Enter without typing anything.")
        print("-" * 50)
        
        for sender in unique_senders:
            new_name = input(f"Rename '{sender}' to: ").strip()
            
            # Only add to the mapping dictionary if the user actually typed a new name
            if new_name:
                rename_mapping[sender] = new_name
                
        # If the mapping dictionary has entries, apply them to the DataFrame. 
        # The .replace() function efficiently hunts down every instance of the old 
        # keys in the 'Sender' column and swaps them with the new string values.
        if rename_mapping:
            df['Sender'] = df['Sender'].replace(rename_mapping)
            print("\n✅ Participants renamed successfully!")
        else:
            print("\nNo names were changed.")
            
    return df

# ==========================================
# MAIN SCRIPT EXECUTION
# ==========================================
if __name__ == "__main__":
    # 1. Determine the input file path. We first check if the user passed it directly 
    # in the terminal (e.g., 'python script.py chat.txt'). If not, we prompt them for it.
    if len(sys.argv) > 1:
        file_path = sys.argv[1] 
    else:
        file_path = input("Please enter the path to your WhatsApp chat export file (.txt): ").strip()

    # 2. Validate that the specified file actually exists on the system to prevent crashes.
    if not os.path.isfile(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        sys.exit(1)
        
    # 3. Parse the raw text into our structured DataFrame.
    print(f"\nParsing '{file_path}'...")
    df = parse_whatsapp_chat(file_path)
    
    # 4. Trigger the interactive renaming function.
    df = rename_participants(df)
    
    # 5. Generate a dynamic output filename based on the original file, and save 
    # the finalized DataFrame to a CSV format without the numerical index column.
    output_filename = "parsed_" + os.path.splitext(os.path.basename(file_path))[0] + ".csv"
    df.to_csv(output_filename, index=False, encoding='utf-8')
    
    # 6. Print a success message and a quick preview to confirm everything worked.
    print("\n" + "="*50)
    print("✅ PROCESS COMPLETE!")
    print(f"Your clean data has been saved as: {output_filename}")
    print("="*50 + "\n")
    
    print("Quick Preview of your final data:")
    print(df[['Date', 'Sender', 'Message']].head(3))
