from flask import Flask, render_template, request, jsonify
from collections import defaultdict
import random

# Initialize the Flask application
app = Flask(__name__)

# Define the days of the week
DAYS = (
    "Monday", 
    "Tuesday", 
    "Wednesday", 
    "Thursday", 
    "Friday", 
    "Saturday", 
    "Sunday"
)

def assign_workers_to_sections(workers_schedule, workers, sections):
    """
    Assigns workers to sections based on their availability in the workers_schedule.

    workers_schedule: Dictionary where the key is a day of the week, 
                      and the value is a list of workers available that day.
    workers: List of all workers.
    sections: The number of sections to assign workers to each day.

    Returns: A dictionary with the schedule for each day of the week, 
             showing which worker is assigned to which section.
    """
    
    # Initialize the weekly schedule for each day with empty sections
    weekly_schedule = {day: {} for day in workers_schedule.keys()}

    # Create a history for each worker tracking their assigned sections (0 means not assigned)
    schedule_history = {worker: [0] * sections for worker in workers}
    print(f'{schedule_history=}')  # Debug: print the initial schedule history

    # Loop through each day in the workers' schedule
    for day, workers in workers_schedule.items():
        # Create an empty dictionary to track which worker is assigned to which section for the day
        daily_sections = {f'Section {i+1}': "None" for i in range(sections)}
        recycled_people = []  # Keep track of workers who were not assigned any section

        print(f'{daily_sections=}')  # Debug: print the daily sections before assignments
        print(f'{workers=}')  # Debug: print the list of workers available for the day
        
        # Loop through each worker available on the current day
        for worker in workers:
            print(f'{worker=}')  # Debug: print the worker being processed

            # If the worker has no previous assignments, reset their schedule history
            if 0 not in schedule_history[worker]:
                schedule_history[worker] = [0] * sections

            # Try to assign the worker to a section if they haven't been assigned yet
            for i, availability in enumerate(schedule_history[worker]):
                # If the worker is available and the section is free, assign them
                if availability == 0 and daily_sections[f'Section {i+1}'] == "None":
                    daily_sections[f'Section {i+1}'] = worker
                    schedule_history[worker][i] = 1  # Mark the section as occupied for this worker
                    print(f'{daily_sections=}')  # Debug: print updated daily sections
                    break  # Break out of the loop once the worker is assigned to a section
                
                # If all sections are checked, add the worker to the recycled list
                if i == sections - 1:
                    recycled_people.append(worker)

        # Debug: print recycled workers who could not be assigned initially
        print(f'{recycled_people=}')
        
        # Reassign recycled workers to any remaining free sections
        for worker in recycled_people:
            print(f'{worker=}')  # Debug: print the recycled worker
            for i, curr_sex in enumerate(daily_sections.values()):
                if curr_sex == "None":  # Find an empty section
                    daily_sections[f'Section {i+1}'] = worker
                    schedule_history[worker][i] = 1  # Mark the section as occupied

        # Add the assigned daily sections to the weekly schedule
        weekly_schedule[day] = daily_sections

    # Debug: print the final weekly schedule
    print(f'{weekly_schedule=}')
    return weekly_schedule

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route to generate the schedule based on user input
@app.route('/generate_schedule', methods=['POST'])
def generate_schedule():
    try:
        # Get the workers and sections from the form input
        workers = request.form['workers'].splitlines()
        sections = int(request.form['sections'])

        # Clean up the worker list, removing empty lines
        workers = [worker.strip() for worker in workers if worker.strip()]

        # Create a dictionary to store the workers' schedule
        workers_schedule = {}
        
        # Populate the workers' schedule based on form input for each day
        for day in DAYS:
            workers_schedule[day] = []
            for worker in workers:
                checkbox_name = f"{worker}-day-{day}"
                if request.form.get(checkbox_name):  # If the worker is assigned to this day
                    workers_schedule[day].append(worker)

        # Generate the schedule by assigning workers to sections
        schedule = assign_workers_to_sections(workers_schedule, workers, sections)

        # Return the schedule, ensuring the days are ordered
        ordered_schedule = {day: schedule[day] for day in DAYS}
        return jsonify(ordered_schedule)

    except ValueError as e:
        # Handle any value errors (e.g., invalid sections input)
        return jsonify({"error": str(e)}), 400

# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)
