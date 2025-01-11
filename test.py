import random

def assign_workers_to_sections(workers_schedule, sections):
    # Initialize the weekly schedule
    weekly_schedule = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

    # Track previous section assignments for each worker
    worker_previous_sections = {worker: [] for workers in workers_schedule.values() for worker in workers}

    for day, workers in workers_schedule.items():
        if len(workers) != len(sections):
            raise ValueError(f"The number of workers for {day} must match the number of sections.")

        # Shuffle workers to randomize the starting order
        random.shuffle(workers)

        daily_assignment = {}
        available_sections = sections.copy()

        for worker in workers:
            # Find a section the worker has not been assigned to recently
            recent_assignments = worker_previous_sections[worker][-len(sections):]
            possible_sections = [section for section in available_sections if section not in recent_assignments]

            if not possible_sections:
                # If no valid section is found, fallback to any available section
                possible_sections = available_sections.copy()

            # Assign the worker to the first valid section
            assigned_section = possible_sections[0]
            daily_assignment[assigned_section] = worker

            # Update tracking
            worker_previous_sections[worker].append(assigned_section)
            available_sections.remove(assigned_section)

        weekly_schedule[day] = daily_assignment

    return weekly_schedule

# Example Usage
if __name__ == "__main__":
    # Define which workers are available on each day with six workers total
    workers_schedule = {
        "Monday": ["Alice", "Bob"],
        "Tuesday": ["Alice", "Charlie"],
        "Wednesday": ["Charlie", "Bob"],
        "Thursday": ["Alice", "Charlie"],
        "Friday": ["Alice", "Bob"],
        "Saturday": ["Charlie", "Bob"],
        "Sunday": ["Alice", "Charlie"]
    }
    sections = ["Section 1", "Section 2"]

    schedule = assign_workers_to_sections(workers_schedule, sections)
    for day, assignments in schedule.items():
        print(f"{day}:")
        for section, worker in assignments.items():
            print(f"  {section}: {worker}")
