from flask import Flask, render_template, redirect, url_for, request, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import time
from flask import Flask, session, redirect, url_for, render_template
from gspread import Client
from gspread.exceptions import APIError
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'rajendra2004'  # Your secret key

# Google Sheets API setup
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

def open_spreadsheet_with_retry(url, retries=5):
    for attempt in range(retries):
        try:
            return client.open_by_url(url)
        except APIError as e:
            if e.response.status_code == 429:  # Too many requests
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Quota exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise  # Raise other API errors
    raise Exception("Failed to open spreadsheet after multiple retries.")

# Open the Google Sheet by URL
spreadsheet = open_spreadsheet_with_retry("https://docs.google.com/spreadsheets/d/12fAh8hX5dWUB4NUafbxEo_sMZRYxV76IrfxqZiV4ZD4/edit")

# Access the 'users' and 'timetable' sheets
users_sheet = spreadsheet.worksheet("users")
timetable_sheet = spreadsheet.worksheet("timetable")


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()  # Strip any leading/trailing spaces
        password = request.form['password'].strip()  # Strip any leading/trailing spaces
        
        # Fetch existing users from the users sheet
        existing_users = users_sheet.get_all_records()  # Fetch existing users from the users sheet
        
        # Check if the username exists
        user_found = False
        for user in existing_users:
            print("Checking User:", user)  # Debugging output
            if user['Username'] == username:  # Check if the username matches
                user_found = True  # Mark that the user was found
                print("Input Password:", password)  # Debugging output
                print("Stored Password:", str(user['Password']))  # Convert stored password to string for comparison
                if str(user['Password']) == password:  # Check if the password matches
                    session['username'] = username
                    return redirect(url_for('home'))
                else:
                    return "Invalid password.", 401  # Unauthorized if password is incorrect
        
        # If the username was not found, redirect to the registration page
        if not user_found:
            return redirect(url_for('register'))  # Redirect to register if username doesn't exist

    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Retrieve user information from the users sheet
    existing_users = users_sheet.get_all_records()  # Fetch existing users from the users sheet
    user_info = next((user for user in existing_users if user['Username'] == session['username']), None)

    if user_info is None:
        return "User  not found.", 404  # Handle case where user info is not found

    return render_template('home.html', username=session['username'], user_info=user_info)

from flask import Flask, render_template, session, redirect, url_for
from datetime import datetime, timedelta
import gspread  # Assuming you're using gspread to interact with Google Sheets
import logging
@app.route('/view_timetable')
def view_timetable():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Retrieve user information to filter timetable
    existing_users = users_sheet.get_all_records()
    user_info = next((user for user in existing_users if user['Username'] == session['username']), None)

    if user_info is None:
        return "User  not found.", 404  # Handle case where user info is not found

    current_day = datetime.now().strftime('%A')  # Get the current day of the week
    current_time = datetime.now().time()  # Get the current time

    # Read timetable data from the timetable sheet
    timetable_data = timetable_sheet.get_all_records()  # Fetch all records from the timetable sheet

    # Log current day and user info for debugging
    logging.debug(f"Current Day: {current_day}")
    logging.debug(f"User  Info: {user_info}")

    # Filter timetable data for the current day and matching user info
    filtered_timetable = [
        {
            'start_time': entry['START TIME'],
            'end_time': entry['END TIME'],
            'subject': entry['SUBJECT'],
            'room_number': entry['ROOM NUMBER']
        }
        for entry in timetable_data 
        if entry.get('DAY', '').strip().upper() == current_day.upper() and
           entry.get('SCHOOL', '').strip().upper() == user_info['School'].upper() and
           entry.get('SEMESTER', '') == str(user_info['Semester']) and
           entry.get('SECTION', '').strip().upper() == user_info['Section'].upper()
    ]

    # Log filtered timetable
    logging.debug(f"Filtered Timetable: {filtered_timetable}")

    # Find the next class
    next_class = None
    for entry in filtered_timetable:
        start_time = datetime.strptime(entry['start_time'], '%H:%M:%S').time()
        if start_time > current_time:
            next_class = entry
            break

    return render_template('view_timetable.html', 
                           timetable=filtered_timetable, 
                           current_day=current_day, 
                           next_class=next_class, 
                           current_time=current_time)
@app.route('/view_timetable_next_day')
def view_timetable_next_day():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Retrieve user information to filter timetable
    existing_users = users_sheet.get_all_records()
    user_info = next((user for user in existing_users if user['Username'] == session['username']), None)

    if user_info is None:
        return "User  not found.", 404  # Handle case where user info is not found

    # Logic to get the next day's timetable
    next_day = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%A')  # Get the next day of the week
    current_time = datetime.datetime.now().time()  # Get the current time

    # Read timetable data from the timetable sheet
    timetable_data = timetable_sheet.get_all_records()  # Fetch all records from the timetable sheet
    
    # Debugging output
    logging.debug(f"Next Day: {next_day}")
    logging.debug(f"User  Info: {user_info}")

    # Filter timetable data for the next day and matching user info
    filtered_timetable = [
        {
            'start_time': entry['START TIME'],
            'end_time': entry['END TIME'],
            'subject': entry['SUBJECT'],
            'room_number': entry['ROOM NUMBER']
        }
        for entry in timetable_data 
        if entry.get('DAY', '').strip() == next_day and 
           entry.get('SCHOOL', '').strip() == user_info['School'] and 
           entry.get('SEMESTER', '') == user_info['Semester'] and 
           entry.get('SECTION', '').strip() == user_info['Section']
    ]

    # Debugging output
    logging.debug(f"Filtered Timetable for Next Day: {filtered_timetable}")

    return render_template('view_timetable.html', 
                           timetable=filtered_timetable, 
                           current_day=next_day, 
                           next_class=None,  # No next class for the next day view
                           current_time=current_time)

@app.route('/add_timetable', methods=['GET', 'POST'])
def add_timetable():
    if request.method == 'POST':
        # Get data from the form
        day = request.form['day']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        school = request.form['school']
        semester = request.form['semester']
        section = request.form['section']
        room_number = request.form['room_number']
        subject = request.form['subject']

        # Open the time2 sheet
        time2_sheet = client.open('College Mangement').worksheet('time2')

        # Append the new timetable entry
        time2_sheet.append_row([day, start_time, end_time, school, semester, section, room_number, subject])

        return redirect(url_for('view_timetable'))  # Redirect back to the view timetable page

    return render_template('add_timetable.html')  # Render the add timetable form


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if the 'users' sheet exists, if not create it
    try:
        # Get all worksheets
        worksheets = spreadsheet.worksheets()
        sheet_names = [sheet.title for sheet in worksheets]

        # Check if 'users' sheet exists
        if 'users' not in sheet_names:
            # Create the 'users' sheet
            users_sheet = spreadsheet.add_worksheet(title="users", rows="100", cols="9")
            # Set up the header row
            users_sheet.append_row(["Username", "Password", "Email", "Student Name", "Roll Number", "School", "Branch", "Semester", "Section"])
        else:
            # Access the existing 'users' sheet
            users_sheet = spreadsheet.worksheet("users")

        # Check if headers are already present
        existing_headers = users_sheet.row_values(1)  # Get the first row (headers)
        if not existing_headers or len(existing_headers) < 9:  # Check if headers are missing or incomplete
            users_sheet.clear()  # Clear the sheet if headers are missing
            users_sheet.append_row(["Username", "Password", "Email", "Student Name", "Roll Number", "School", "Branch", "Semester", "Section"])

    except Exception as e:
        return f"An error occurred while accessing the spreadsheet: {e}", 500  # Internal Server Error

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        student_name = request.form['student_name']
        roll_number = request.form['roll_number']
        school = request.form['school']
        branch = request.form['branch']
        semester = request.form['semester']
        section = request.form['section']
        
        # Check if the username already exists
        existing_users = users_sheet.get_all_records()  # Fetch existing users from the users sheet
        if any(user['Username'] == username for user in existing_users):
            return "Username already exists. Please choose a different one.", 400  # Bad Request
        
        # Store user information in the users sheet
        users_sheet.append_row([username, password, email, student_name, roll_number, school, branch, semester, section])
        
        return redirect(url_for('login'))  # Redirect to the login page after successful registration

    return render_template('register.html')  # Render the registration form

from datetime import datetime, timedelta

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Read data from the timetable sheet
    timetable_data = timetable_sheet.get_all_records()  # Fetch all records from the timetable sheet

    # Get the current time
    current_time = datetime.now()
    current_hour = current_time.hour
    current_minute = current_time.minute

    # Logic to filter occupied rooms and determine availability
    occupied_rooms = set()  # Set to keep track of occupied rooms
    next_classes = {}  # Dictionary to store the next class time for each room

    for entry in timetable_data:
        room_number = entry['ROOM NUMBER']
        start_class_time = datetime.strptime(entry['START TIME'], '%H:%M:%S').time()
        end_class_time = datetime.strptime(entry['END TIME'], '%H:%M:%S').time()

        # Check if the current time is within the class time
        if start_class_time <= current_time.time() < end_class_time:
            occupied_rooms.add(room_number)  # Add room number to the occupied set
        else:
            # Store the next class time for each room
            if room_number not in next_classes or start_class_time < next_classes[room_number]:
                next_classes[room_number] = start_class_time

    # Get all unique room numbers from the timetable data
    all_rooms = {entry['ROOM NUMBER'] for entry in timetable_data}

    # Determine empty rooms and their availability
    empty_rooms = []
    for room in all_rooms:
        if room not in occupied_rooms:
            # Calculate the availability until the next class
            next_class_time = next_classes.get(room)
            if next_class_time:
                next_class_datetime = datetime.combine(current_time.date(), next_class_time)
                availability_until = next_class_datetime.strftime('%H:%M')
                empty_rooms.append((room, availability_until))
            else:
                # If no next class, consider it vacant indefinitely
                empty_rooms.append((room, "Indefinite"))

    return render_template('dashboard.html', username=session['username'], empty_rooms=empty_rooms, current_time=current_time.strftime('%H:%M'))

from datetime import datetime, timedelta

@app.route('/view_empty_rooms')
def view_empty_rooms():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Read data from the timetable sheet
    timetable_data = timetable_sheet.get_all_records()  # Fetch all records from the timetable sheet
    current_time = datetime.now()  # Get the current time

    # Define the time range for checking occupancy
    start_time = current_time.replace(second=0, microsecond=0)
    end_time = (current_time + timedelta(hours=1)).replace(second=0, microsecond=0)

    # Logic to filter empty rooms and calculate availability
    occupied_rooms = set()  # Set to keep track of occupied rooms
    next_classes = {}  # Dictionary to store the next class time for each room

    for entry in timetable_data:
        room_number = entry['ROOM NUMBER']
        start_class_time = datetime.strptime(entry['START TIME'], '%H:%M:%S').time()
        end_class_time = datetime.strptime(entry['END TIME'], '%H:%M:%S').time()

        # Check if the current time is within the class time
        if start_class_time <= start_time.time() < end_class_time or start_class_time < end_time.time() <= end_class_time:
            occupied_rooms.add(room_number)  # Add room number to the occupied set
        else:
            # Store the next class time for each room
            if room_number not in next_classes or start_class_time < next_classes[room_number]:
                next_classes[room_number] = start_class_time

    # Get all unique room numbers from the timetable data
    all_rooms = {entry['ROOM NUMBER'] for entry in timetable_data}

    # Determine empty rooms and calculate availability
    empty_rooms = []
    for room in all_rooms:
        if room not in occupied_rooms:
            # Calculate the availability until the next class
            next_class_time = next_classes.get(room)
            if next_class_time:
                next_class_datetime = datetime.combine(current_time.date(), next_class_time)
                availability_duration = next_class_datetime - current_time
                empty_rooms.append((room, next_class_time.strftime('%H:%M')))
            else:
                # If no next class, consider it vacant indefinitely
                empty_rooms.append((room, "Indefinite"))

    return render_template('view_empty_rooms.html', empty_rooms=empty_rooms, current_time=current_time.strftime('%H:%M'))

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
