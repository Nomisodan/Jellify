import sqlite3
from flask import Flask, request, render_template, redirect, url_for, flash
from datetime import datetime, timedelta

app = Flask(__name__)
# Required for flashing messages
app.secret_key = 'your_secret_key'

# Database setup, creates the database and table
def init_db():
    with sqlite3.connect('appointments.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            service TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL
        )''')
        conn.commit()

# Call the init_db function to create the table when the app runs
init_db()

# Function to generate time slots every 30 minutes, in 2-hour blocks in the appointment time forms
def generate_time_slots(start_time="09:00", end_time="17:00", interval=30):
    time_slots = []
    current_time = datetime.strptime(start_time, "%H:%M")
    end_time = datetime.strptime(end_time, "%H:%M")

    while current_time <= end_time:
        time_slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=interval)
    return time_slots

# Home route for displaying the booking form and handling POST requests
@app.route('/', methods=['GET', 'POST'])
def home():
    # Get today's date in YYYY-MM-DD format
    today = datetime.today().date()

    # Generate available time slots (from 9 AM to 5 PM with 30-minute increments)
    time_slots = generate_time_slots(start_time="09:00", end_time="17:00", interval=30)

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        service = request.form.get('service')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')

        # Check if the appointment date is in the past
        if datetime.strptime(appointment_date, "%Y-%m-%d").date() < today:
            flash("You cannot book an appointment for a past date.", "error")
            return redirect(url_for('home'))

        # Check if the appointment time is already taken
        with sqlite3.connect('appointments.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM appointments WHERE appointment_date = ? AND appointment_time = ?''',
                           (appointment_date, appointment_time))
            existing_appointment = cursor.fetchone()

            if existing_appointment:
                flash("The selected time slot is already booked. Please choose a different time.", "error")
                return redirect(url_for('home'))

        # Simple validation for required fields
        if not name or not email or not phone or not service or not appointment_date or not appointment_time:
            flash("All fields are required!", "error")
            return redirect(url_for('home'))

        try:
            # Insert the appointment into the database appointments.db
            with sqlite3.connect('appointments.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO appointments (name, email, phone, service, appointment_date, appointment_time)
                                VALUES (?, ?, ?, ?, ?, ?)''', (name, email, phone, service, appointment_date, appointment_time))
                conn.commit()

            return redirect(url_for('thank_you', name=name, service=service, appointment_date=appointment_date, appointment_time=appointment_time))
        except sqlite3.Error as e:
            flash(f"Error occurred: {e}", "error")
            return redirect(url_for('home'))

    # Filter out the booked time slots for the selected date
    if request.method == 'GET':
        booked_slots = []
        # If the user selected a date, filter out unavailable slots
        appointment_date = request.args.get('appointment_date')
        if appointment_date:
            with sqlite3.connect('appointments.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT appointment_time FROM appointments WHERE appointment_date = ?''', (appointment_date,))
                booked_slots = [row[0] for row in cursor.fetchall()]

            # Remove booked slots from the list of available time slots
            time_slots = [time for time in time_slots if time not in booked_slots]

    # If it's a GET request, render the booking form
    return render_template('jellify.html', time_slots=time_slots, today=today)

# Route for the "Thank You" page
@app.route('/thank-you')
def thank_you():
    # Retrieve data passed via query parameters
    name = request.args.get('name')
    service = request.args.get('service')
    appointment_date = request.args.get('appointment_date')
    appointment_time = request.args.get('appointment_time')

    return render_template('thank_you.html', name=name, service=service, appointment_date=appointment_date, appointment_time=appointment_time)

#route for terms and conditions
@app.route('/terms')
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    app.run(debug=True)
