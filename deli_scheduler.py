import pandas as pd
from datetime import datetime, timedelta
import os

def parse_shift_time(shift_string, target_day):
    try:
        shifts = shift_string.split(', ')
        for shift in shifts:
            parts = shift.split()
            if len(parts) < 2:
                continue  # Skip this shift if it doesn't have enough parts
            day = parts[0]
            if day[:3].lower() == target_day[:3].lower():
                times = parts[-1]  # Assume the last part contains the times
                start_time, end_time = times.split('-')
                return datetime.strptime(start_time, "%H:%M").time(), datetime.strptime(end_time, "%H:%M").time()
    except Exception as e:
        print(f"Error parsing shift time for '{shift_string}': {e}")
    return None, None

def generate_daily_schedule(df, target_date):
    target_day = target_date.strftime('%a')
    print(f"\nSchedule for {target_date.strftime('%A, %B %d, %Y')}")
    print("-" * 120)
    print(f"{'Employee Name':<20} {'Job Title':<25} {'Shift Time':<20} {'Roles':<55}")
    print("-" * 120)

    scheduled_employees = []

    for _, employee in df.iterrows():
        start_time, end_time = parse_shift_time(employee['Availability'], target_day)
        if start_time and end_time:
            scheduled_employees.append((
                employee['Employee Name'],
                employee['Job Title'],
                (start_time, end_time),
                employee['Roles']
            ))

    # Sort employees by shift start time
    scheduled_employees.sort(key=lambda x: x[2][0])

    for name, title, (start_time, end_time), roles in scheduled_employees:
        print(f"{name:<20} {title:<25} {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M'):<14} {roles[:55]}")

def generate_weekly_schedule(df, start_date):
    print(f"Weekly Schedule")
    print(f"Week of {start_date.strftime('%B %d, %Y')}")
    print()

    for i in range(7):
        current_date = start_date + timedelta(days=i)
        generate_daily_schedule(df, current_date)
        print()

# Get the CSV file path from the user
while True:
    file_path = input("Enter the path to your CSV file (or just the filename if it's in the same directory): ")
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            break
        except Exception as e:
            print(f"Error reading the file: {e}")
            print("Please make sure the file is a valid CSV.")
    else:
        print("File not found. Please enter a valid file path.")

print("Columns in the DataFrame:")
print(df.columns)
print("\nSample data:")
print(df.head())

# Print unique values in the Availability column
print("\nUnique values in the Availability column:")
print(df['Availability'].unique())

# Get user input for the start date of the week
while True:
    date_input = input("Enter the start date of the week (YYYY-MM-DD): ")
    try:
        start_date = datetime.strptime(date_input, "%Y-%m-%d")
        break
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")

generate_weekly_schedule(df, start_date)