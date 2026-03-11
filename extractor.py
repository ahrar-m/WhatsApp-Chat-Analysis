import os
import zipfile

def extract_and_rename_chat():
    # 1. Find all .zip files in the current working directory
    zip_files = [f for f in os.listdir('.') if f.endswith('.zip')]
    
    if not zip_files:
        print("❌ No .zip files found in the current directory.")
        return

    # If there are multiple zips, default to the first one found
    target_zip = zip_files[0]
    if len(zip_files) > 1:
        print(f"⚠️ Multiple zip files found. Defaulting to: {target_zip}")

    try:
        # 2. Open the zip file and look for a .txt file
        with zipfile.ZipFile(target_zip, 'r') as z:
            txt_files = [f for f in z.namelist() if f.endswith('.txt')]
            
            if not txt_files:
                print(f"❌ No .txt files found inside '{target_zip}'.")
                return
            
            # Assume the first .txt file is the chat export
            target_txt = txt_files[0]
            
            # 3. Ask the user for confirmation
            print("\n--- Confirmation Required ---")
            print(f"📦 Zip Archive : {target_zip}")
            print(f"📄 Target File : {target_txt}")
            
            confirm = input("\nExtract and rename this file to 'chat.txt'? (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                # 4. Extract directly into a new file named 'chat.txt'
                # We read it in binary ('wb') to safely handle emojis and special characters
                with z.open(target_txt) as source_file:
                    with open('chat.txt', 'wb') as output_file:
                        output_file.write(source_file.read())
                
                print("✅ Success! Chat exported to 'chat.txt'.")
            else:
                print("🛑 Operation cancelled by user.")
                
    except zipfile.BadZipFile:
        print(f"❌ Error: '{target_zip}' is not a valid zip file or is corrupted.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    extract_and_rename_chat()