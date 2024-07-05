import pandas as pd
from datetime import datetime, timedelta
import os

def parse_shift_time(shift_string, target_day):
    try:
        shifts = shift_string.split(', ')
        for shift in shifts:
            parts = shift.split()
            if len(parts) < 2:
                continue
            day, times = parts[0], parts[-1]
            if day[:3].lower() == target_day[:3].lower():
                start_time, end_time = times.split('-')
                return datetime.strptime(start_time, "%H:%M").time(), datetime.strptime(end_time, "%H:%M").time()
    except Exception as e:
        print(f"Error parsing shift time for '{shift_string}': {e}")
    return None, None

def adjust_shift_duration(start_time, end_time, employment_status):
    shift_duration = datetime.combine(datetime.min, end_time) - datetime.combine(datetime.min, start_time)
    if employment_status == 'Part-Time':
        min_duration = timedelta(hours=4)
        max_duration = timedelta(hours=8)
    else:  # Full-Time
        min_duration = timedelta(hours=8)
        max_duration = timedelta(hours=10)
    
    if shift_duration < min_duration:
        end_time = (datetime.combine(datetime.min, start_time) + min_duration).time()
    elif shift_duration > max_duration:
        end_time = (datetime.combine(datetime.min, start_time) + max_duration).time()
    
    return start_time, end_time

def schedule_meal_break(start_time, end_time, staff_count):
    shift_duration = datetime.combine(datetime.min, end_time) - datetime.combine(datetime.min, start_time)
    meal_duration = timedelta(minutes=30) if shift_duration <= timedelta(hours=6) else timedelta(hours=1)

    possible_break_starts = [
        datetime.combine(datetime.min, start_time) + timedelta(hours=2),
        datetime.combine(datetime.min, start_time) + (shift_duration - meal_duration) / 2,
        datetime.combine(datetime.min, end_time) - timedelta(hours=2) - meal_duration
    ]

    for break_start in possible_break_starts:
        break_end = break_start + meal_duration
        if is_break_time_valid(break_start.time(), break_end.time(), staff_count):
            return break_start.time(), break_end.time()

    meal_start = datetime.combine(datetime.min, start_time) + (shift_duration - meal_duration) / 2
    meal_end = meal_start + meal_duration
    return meal_start.time(), meal_end.time()

def is_break_time_valid(break_start, break_end, staff_count):
    morning_requirement = break_start < datetime.strptime("08:00", "%H:%M").time() and staff_count > 6
    midday_requirement = (datetime.strptime("10:30", "%H:%M").time() <= break_start < datetime.strptime("14:00", "%H:%M").time()) and staff_count > 10
    evening_requirement = (datetime.strptime("21:00", "%H:%M").time() <= break_start < datetime.strptime("23:00", "%H:%M").time()) and staff_count > 4
    return not (morning_requirement or midday_requirement or evening_requirement)

def format_time_range(start_time, end_time):
    return f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"

def count_employees_in_timeframe(employees, start_hour, end_hour):
    count = 0
    for employee in employees:
        start_time = employee[2][0]
        end_time = employee[2][1]
        if (start_time.hour < end_hour and end_time.hour > start_hour) or (start_time.hour == start_hour) or (end_time.hour == end_hour):
            count += 1
    return count

def ensure_late_night_coverage(scheduled_employees, all_employees, max_employees_per_day):
    late_night_count = sum(1 for e in scheduled_employees if e[2][1] == datetime.strptime("23:00", "%H:%M").time())
    if late_night_count < 4:
        additional_needed = 4 - late_night_count
        
        candidates = sorted(
            [e for e in all_employees if e not in scheduled_employees and e[2][1] >= datetime.strptime("21:00", "%H:%M").time()],
            key=lambda x: x[2][1],
            reverse=True
        )
        
        for employee in candidates:
            if additional_needed == 0 or len(scheduled_employees) >= max_employees_per_day:
                break
            
            start_time, end_time = employee[2]
            
            if end_time == datetime.strptime("23:00", "%H:%M").time():
                scheduled_employees.append(employee)
                additional_needed -= 1
            elif end_time >= datetime.strptime("21:00", "%H:%M").time():
                shift_duration = datetime.combine(datetime.min, end_time) - datetime.combine(datetime.min, start_time)
                max_duration = timedelta(hours=10 if employee[5] == 'Full-Time' else 8)
                required_duration = datetime.combine(datetime.min, datetime.strptime("23:00", "%H:%M").time()) - datetime.combine(datetime.min, start_time)
                
                if required_duration <= max_duration:
                    new_start_time = (datetime.combine(datetime.min, datetime.strptime("23:00", "%H:%M").time()) - shift_duration).time()
                    employee = employee[:2] + ((new_start_time, datetime.strptime("23:00", "%H:%M").time()),) + employee[3:]
                    scheduled_employees.append(employee)
                    additional_needed -= 1

    return scheduled_employees

def generate_daily_schedule(df, target_date, weekly_late_night_counts):
    target_day = target_date.strftime('%a')
    print(f"\nDaily Overview")
    print(f"{target_date.strftime('%m/%d/%Y')}")
    print("-" * 100)
    print(f"{'Associate':<20} {'Jobs':<20} {'Shift/Roles':<40} {'Meals':<20}")
    print("-" * 100)

    all_employees = []
    for _, employee in df.iterrows():
        start_time, end_time = parse_shift_time(employee['Availability'], target_day)
        if start_time and end_time:
            all_employees.append((
                employee['Employee Name'],
                employee['Job Title'],
                (start_time, end_time),
                None,  # Placeholder for meal break
                employee['Roles'],
                employee['Employment Status']
            ))

    max_employees_per_day = 28
    min_closing_count = 4
    max_early_morning_count = 6  # Strict limit for early morning shifts

    scheduled_employees = []

    # Define smaller shift windows based on roles
    shift_windows = [
        (datetime.strptime("06:00", "%H:%M").time(), datetime.strptime("10:00", "%H:%M").time(), "DL-AM Production"),
        (datetime.strptime("10:00", "%H:%M").time(), datetime.strptime("14:00", "%H:%M").time(), "DL-Subs Service"),
        (datetime.strptime("14:00", "%H:%M").time(), datetime.strptime("18:00", "%H:%M").time(), "DL-Hot Case Service"),
        (datetime.strptime("18:00", "%H:%M").time(), datetime.strptime("22:00", "%H:%M").time(), "DL-Traditional Service")
    ]

    def schedule_shift_window(shift_window, scheduled_employees, all_employees, max_count_per_window=4):
        nonlocal max_employees_per_day
        group_count = 0
        for employee in all_employees:
            if group_count >= max_count_per_window or len(scheduled_employees) >= max_employees_per_day:
                break
            if employee not in scheduled_employees:
                start_time, end_time = employee[2]
                if start_time >= shift_window[0] and end_time <= shift_window[1]:
                    scheduled_employees.append(employee[:2] + ((start_time, end_time),) + (shift_window[2],) + employee[4:])
                    group_count += 1

    # Schedule early morning shifts with strict limit
    schedule_shift_window(shift_windows[0], scheduled_employees, all_employees, max_early_morning_count)

    # Schedule remaining employees in other shift windows
    remaining_slots = max_employees_per_day - len(scheduled_employees)
    for shift_window in shift_windows[1:]:
        schedule_shift_window(shift_window, scheduled_employees, all_employees, remaining_slots // len(shift_windows[1:]))

    # Ensure minimum closing coverage
    if len([e for e in scheduled_employees if e[2][1] == datetime.strptime("23:00", "%H:%M").time()]) < min_closing_count:
        scheduled_employees = ensure_late_night_coverage(scheduled_employees, all_employees, max_employees_per_day)

    # Initialize hourly staff count
    hourly_staff_count = [0] * 24
    for employee in scheduled_employees:
        for hour in range(employee[2][0].hour, employee[2][1].hour):
            hourly_staff_count[hour] += 1

    # Adjust shift durations
    for i, employee in enumerate(scheduled_employees):
        start_time, end_time = adjust_shift_duration(employee[2][0], employee[2][1], employee[5])
        scheduled_employees[i] = employee[:2] + ((start_time, end_time),) + employee[3:]

    # Schedule meal breaks
    for i, employee in enumerate(scheduled_employees):
        meal_start, meal_end = schedule_meal_break(employee[2][0], employee[2][1], min(hourly_staff_count[employee[2][0].hour:employee[2][1].hour]))
        scheduled_employees[i] = employee[:3] + ((meal_start, meal_end),) + employee[4:]

    # Sort final schedule by start time
    scheduled_employees.sort(key=lambda x: x[2][0])

    # Print the schedule
    current_employee = ""
    for name, title, (start_time, end_time), (meal_start, meal_end), roles, _ in scheduled_employees:
        if name != current_employee:
            print(f"{name:<20} {title:<20}", end="")
            current_employee = name
        else:
            print(f"{'':20} {'':20}", end="")

        shift_str = format_time_range(start_time, end_time)
        roles_str = roles[:30]  # Truncate roles to fit
        meal_str = format_time_range(meal_start, meal_end)

        print(f"{shift_str} {roles_str:<30} {meal_str}")

    print(f"\nTotal employees scheduled: {len(scheduled_employees)}")
    print(f"Employees starting at 5:00 AM: {sum(1 for e in scheduled_employees if e[2][0] == datetime.strptime('05:00', '%H:%M').time())}")
    print(f"Employees staying until 11:00 PM: {sum(1 for e in scheduled_employees if e[2][1] == datetime.strptime('23:00', '%H:%M').time())}")
    print(f"Employees present by 8:00 AM: {count_employees_in_timeframe(scheduled_employees, 5, 8)}")
    print(f"Employees present from 10:30 AM to 2:00 PM: {count_employees_in_timeframe(scheduled_employees, 10, 14)}")
    print(f"Employees present after 2:00 PM: {count_employees_in_timeframe(scheduled_employees, 14, 23)}")

    return scheduled_employees, weekly_late_night_counts

def generate_weekly_schedule(df, start_date):
    weekly_late_night_counts = {}
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        _, weekly_late_night_counts = generate_daily_schedule(df, current_date, weekly_late_night_counts)
        print("\n")

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

# Get user input for the start date of the week
while True:
    date_input = input("Enter the start date of the week (YYYY-MM-DD): ")
    try:
        start_date = datetime.strptime(date_input, "%Y-%m-%d")
        break
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")

generate_weekly_schedule(df, start_date)
