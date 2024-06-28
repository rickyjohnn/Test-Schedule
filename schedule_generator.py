import pandas as pd
from datetime import datetime, timedelta

def parse_shift_time(shift_string, target_date):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    target_day = days[target_date.weekday()]
    
    try:
        day_shifts = shift_string.split(', ')
        for day_shift in day_shifts:
            if day_shift.startswith(target_day):
                time_str = day_shift.split(' ')[1].split('-')[0]
                return datetime.strptime(time_str, "%H:%M").time()
    except Exception as e:
        print(f"Error parsing shift time for {shift_string}: {e}")
    return None

def get_shifts_for_date(shifts, target_date):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    target_day = days[target_date.weekday()]
    
    try:
        day_shifts = shifts.split(', ')
        for day_shift in day_shifts:
            if day_shift.startswith(target_day):
                return day_shift
    except Exception as e:
        print(f"Error getting shifts for date: {e}")
    return None

def generate_schedule(df, target_date):
    print("Daily Overview")
    print(target_date.strftime("%m/%d/%Y"))
    print()
    print(f"{'Employee Name':<20} {'Job Title':<25} {'Shift/Roles':<40} {'Meals':<20}")
    print("-" * 105)

    def sort_key(row):
        shift_time = parse_shift_time(row['Work Hours'], target_date)
        return (shift_time or datetime.max.time(), row['Employee Name'])

    try:
        sorted_data = df.sort_values(key=sort_key)
    except Exception as e:
        print(f"Error sorting data: {e}")
        return

    for _, row in sorted_data.iterrows():
        try:
            name = row['Employee Name']
            job = row['Job Title']
            shifts = row['Work Hours']
            roles = row['Roles']
            availability = row['Availability']

            day_shift = get_shifts_for_date(shifts, target_date)
            if day_shift and target_date.strftime("%a") in availability:
                print(f"{name:<20} {job:<25}")
                print(f"{'':<45} {day_shift}")
                print(f"{'':<45} Roles: {roles}")
                print()
        except Exception as e:
            print(f"Error processing employee {row['Employee Name']}: {e}")

# Read the CSV file
try:
    df = pd.read_csv('deli_schedule.csv')
    print("CSV file read successfully.")
    print("Columns in the DataFrame:", df.columns.tolist())
    print("First few rows of data:")
    print(df.head())
except Exception as e:
    print(f"Error reading CSV file: {e}")
    exit()

# Generate schedule for a specific date
target_date = datetime(2024, 6, 25)  # A Tuesday
generate_schedule(df, target_date)