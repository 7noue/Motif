import pandas as pd
import os

# Try to find the 100-film file first, then fall back to the 5000-film file
filename = "motif_mvp_100_local.csv"
if not os.path.exists(filename):
    filename = "motif_mvp_5000_enriched.csv"

print(f"📂 Reading from: {filename}...\n")

try:
    df = pd.read_csv(filename)
    
    # Check if 'title' column exists
    if 'title' in df.columns:
        # Sort them alphabetically so it's easier to read
        titles = sorted(df['title'].tolist())
        
        print(f"🎬 Found {len(titles)} movies:")
        print("-" * 30)
        
        for i, title in enumerate(titles):
            print(f"{i+1}. {title}")
            
    else:
        print("❌ Error: Could not find a 'title' column in the CSV.")
        print(f"Columns found: {df.columns.tolist()}")

except FileNotFoundError:
    print(f"❌ Error: Could not find file '{filename}'. Make sure it is in the same folder as this script.")