import pandas as pd
import sys

print("Script is starting...")
sys.stdout.flush()

# Read the CSV file
try:
    print("Attempting to read CSV file...")
    sys.stdout.flush()
    df = pd.read_csv('deli_schedule.csv')
    print("CSV file read successfully.")
    sys.stdout.flush()

    print("\nColumns in the DataFrame:")
    print(df.columns.tolist())
    sys.stdout.flush()
    
    print("\nFirst few rows of data:")
    print(df.head().to_string())
    sys.stdout.flush()
    
    print("\nData types of columns:")
    print(df.dtypes)
    sys.stdout.flush()
    
    print("\nSample of 'Work Hours' column:")
    print(df['Work Hours'].head())
    sys.stdout.flush()
    
    print("\nSample of 'Availability' column:")
    print(df['Availability'].head())
    sys.stdout.flush()

except Exception as e:
    print(f"Error reading CSV file: {e}")
    sys.stdout.flush()

print("Script has finished running.")
sys.stdout.flush()