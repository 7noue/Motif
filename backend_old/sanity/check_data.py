import pandas as pd
import os

# --- STEP 1: LOAD MASTER DATA ---
# Get the folder where THIS script lives
script_dir = os.path.dirname(os.path.abspath(__file__))

# Go up one level (..) to 'backend', then down into 'data'
input_file = os.path.join(script_dir, "../data/motif_master_data_100.csv")

print(f"📂 Loading master data from: {input_file}...")

try:
    df = pd.read_csv(input_file)
    
    # Check if 'title' column exists
    if 'title' in df.columns:
        # Sort them alphabetically so it's easier to read
        titles = sorted(df['title'].astype(str).tolist())
        
        print(f"🎬 Found {len(titles)} movies:")
        print("-" * 30)
        
        for i, title in enumerate(titles):
            print(f"{i+1}. {title}")
            
    else:
        print("❌ Error: Could not find a 'title' column in the CSV.")
        print(f"Columns found: {df.columns.tolist()}")

except FileNotFoundError:
    print(f"❌ Error: Could not find file at '{input_file}'.")
    print("   Make sure the file exists in the 'backend/data/' folder.")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")