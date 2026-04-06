from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Days of the week in display order
DAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

# Sentinel meaning a worker has never been assigned to a particular section.
# Using -1 makes it sort as "oldest possible" so never-visited sections are
# always preferred over ones the worker has already been in.
NEVER = -1


def assign_workers_to_sections(daily_availability, all_workers, num_sections):
    """
    Assigns workers to sections each day, trying to:
      1. Never put a worker in the same section on back-to-back days (hard rule,
         broken only when truly no other option exists).
      2. Prefer the section the worker has gone the longest without visiting
         (soft rule — full rotation before revisiting).
      3. When multiple workers want the same section, the one who has waited
         longer for it wins; the other falls back to their next-best option.

    Args:
        daily_availability: Dict mapping each day name to the list of workers
                            available that day. e.g. {"Monday": ["Alice", "Bob"]}
        all_workers:        Complete list of all workers (used to initialise
                            history tracking).
        num_sections:       How many sections exist per day.

    Returns:
        A dict mapping each day name to a dict of section assignments.
        e.g. {"Monday": {"Section 1": "Alice", "Section 2": "Bob"}}
    """

    # last_assigned_day[worker][section_index] = the day-index on which that
    # worker was last placed in that section (NEVER = has never been there).
    # A lower value means the worker has gone longer without that section,
    # so lower = more preferred.
    last_assigned_day = {
        worker: [NEVER] * num_sections for worker in all_workers
    }

    section_keys = [f"Section {i + 1}" for i in range(num_sections)]
    weekly_schedule = {}

    for day_index, (day, available_workers) in enumerate(daily_availability.items()):

        # Start each day with every section empty.
        day_assignments = {section: None for section in section_keys}

        def section_preference(worker):
            """
            Returns section indices sorted from most-preferred to least-preferred
            for this worker on this day.

            Sort key per section (ascending = more preferred):
              1. Was this their section yesterday? (True sorts after False, so
                 yesterday's section is pushed to the back.)
              2. How long ago were they last here? (lower last_assigned_day value
                 = longer ago = more preferred, so we sort ascending on it.)
            """
            yesterday_index = day_index - 1  # negative on day 0 — never matches

            def sort_key(section_idx):
                was_here_yesterday = (
                    last_assigned_day[worker][section_idx] == yesterday_index
                )
                last_visit = last_assigned_day[worker][section_idx]
                return (was_here_yesterday, last_visit)

            return sorted(range(num_sections), key=sort_key)

        # Build a ranked preference list for every available worker.
        # preferences[worker] = [most-wanted section idx, ..., least-wanted idx]
        preferences = {worker: section_preference(worker) for worker in available_workers}

        # --- Greedy assignment with conflict resolution ---
        #
        # Each pass: every unassigned worker claims their current top-preference
        # section. If two workers claim the same section, the one who has waited
        # longer wins; the loser drops that section and retries next pass.
        # Repeat until everyone is placed or no sections remain.

        unassigned = list(available_workers)

        while unassigned:
            # --- Phase 1: build claims without modifying preferences yet ---
            # Each worker tentatively claims their current top-preference section.
            # Conflicts are resolved purely by who has waited longer; no preference
            # lists are mutated here so no worker loses their place unfairly.
            claims = {}  # section_idx -> winning worker for this pass

            for worker in unassigned:
                if not preferences[worker]:
                    continue  # no sections left for this worker

                top_idx = preferences[worker][0]

                if top_idx not in claims:
                    claims[top_idx] = worker
                else:
                    # Conflict: worker who visited this section longest ago wins.
                    # Ties go to the current holder.
                    current_holder  = claims[top_idx]
                    holder_last     = last_assigned_day[current_holder][top_idx]
                    challenger_last = last_assigned_day[worker][top_idx]

                    if challenger_last < holder_last:
                        # Challenger waited longer — they win the claim.
                        claims[top_idx] = worker
                    # Loser is determined in Phase 2; we don't pop anything here.

            # --- Phase 2: commit winners, drop the losing section for losers ---
            next_unassigned = []

            for worker in unassigned:
                if not preferences[worker]:
                    # Exhausted all preferences (more workers than sections).
                    continue

                top_idx = preferences[worker][0]

                if claims.get(top_idx) == worker:
                    # This worker won — assign them and record the day.
                    section_key = section_keys[top_idx]
                    day_assignments[section_key] = worker
                    last_assigned_day[worker][top_idx] = day_index
                    preferences[worker].pop(0)  # consume the winning preference
                else:
                    # This worker lost the conflict for top_idx.
                    # Drop that section so they try their next preference next pass.
                    preferences[worker].pop(0)
                    next_unassigned.append(worker)

            # If no progress was made, remaining workers exceed available sections.
            if len(next_unassigned) == len(unassigned):
                break

            unassigned = next_unassigned

        # Mark any sections that went unfilled as "Unassigned".
        for section in section_keys:
            if day_assignments[section] is None:
                day_assignments[section] = "Unassigned"

        weekly_schedule[day] = day_assignments

    return weekly_schedule


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate_schedule", methods=["POST"])
def generate_schedule():
    try:
        # Parse the newline-separated worker list from the form.
        raw_workers = request.form["workers"].splitlines()
        all_workers = [w.strip() for w in raw_workers if w.strip()]

        if not all_workers:
            raise ValueError("Please provide at least one worker.")

        num_sections = int(request.form["sections"])
        if num_sections < 1:
            raise ValueError("Number of sections must be at least 1.")

        # Build the availability dict: for each day, collect workers whose
        # checkbox for that day was ticked.
        daily_availability = {}
        for day in DAYS:
            daily_availability[day] = [
                worker for worker in all_workers
                if request.form.get(f"{worker}-day-{day}")
            ]

        schedule = assign_workers_to_sections(
            daily_availability, all_workers, num_sections
        )

        # Return days in the canonical DAYS order.
        ordered_schedule = {day: schedule[day] for day in DAYS}
        return jsonify(ordered_schedule)

    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True)