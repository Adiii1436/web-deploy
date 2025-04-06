import pandas as pd
import glob
import os

# Directory where your CSVs are stored
csv_folder = 'scrapped_data/'  # Change this to your actual folder path if needed

# Find all CSV files in the folder (you can filter for only assessments*.csv if needed)
csv_files = glob.glob(os.path.join(csv_folder, 'assessments*.csv'))

# Read and combine all CSVs
df_list = [pd.read_csv(f) for f in csv_files]
merged_df = pd.concat(df_list, ignore_index=True)

# Optional: Drop duplicates based on full row or specific column (e.g. 'name')
merged_df.drop_duplicates(inplace=True)

# Save merged DataFrame to a new CSV file
merged_df.to_csv('merged_assessments.csv', index=False)

print(f"Merged {len(csv_files)} files. Final shape: {merged_df.shape}")
