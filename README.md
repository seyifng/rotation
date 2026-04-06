# Work Rotation Scheduler

A lightweight Flask web app that generates weekly section assignments for a team of workers, rotating fairly so no one is stuck in the same section every day.

---

## How It Works

The scheduler uses a **longest-wait** rotation algorithm:

- Each worker tracks the last day they were assigned to each section
- When assigning a day, every worker is given the section they have gone the **longest without** visiting
- A worker is **never assigned the same section on back-to-back days** (hard rule — only broken if there is truly no other option)
- When two workers want the same section, the one who has waited longer wins; the other falls back to their next best option
- Workers who miss days pick up their rotation right where they left off — their history is preserved

---

## Project Structure

```
project/
├── app.py                  # Flask backend + scheduling logic
├── templates/
│   └── index.html          # Frontend UI
└── static/
    └── style.css           # Styles
```

---

## Setup

**Requirements**

- Python 3.8+
- Flask

**Install dependencies**

```bash
pip install flask
```

**Run the app**

```bash
python app.py
```

Then open your browser and go to `http://127.0.0.1:5000`.

---

## Usage

1. **Enter workers** — type one name per line in the text area
2. **Mark availability** — the table auto-populates; check the days each worker is in
3. **Set sections** — enter how many sections need to be filled each day
4. **Generate** — click the button and the schedule appears below as a card grid

---

## Algorithm Details

### Assignment flow (per day)

1. Build a ranked preference list for every available worker — sections sorted by how long ago they were last there, with yesterday's section pushed to the back
2. Each worker tentatively claims their top preference
3. If two workers claim the same section, the one who visited it longest ago wins
4. Losers drop that section and retry with their next preference
5. Passes repeat until all workers are placed or no open sections remain
6. Any section still empty after all passes is marked **Unassigned**

### Known tradeoffs

| Scenario                                        | Behavior                                                    |
| ----------------------------------------------- | ----------------------------------------------------------- |
| More workers than sections                      | Extra workers are not assigned — sections never double-fill |
| Fewer workers than sections                     | Leftover sections show "Unassigned"                         |
| Worker returns after missing days               | History is intact — rotation resumes naturally              |
| Only one section left and worker was just there | Back-to-back rule is broken — no other option               |

---

## Customization

- **Add more days or change the week structure** — edit the `DAYS` tuple at the top of `app.py`
- **Change section naming** — section keys are generated as `Section 1`, `Section 2`, etc.; update `section_keys` in `assign_workers_to_sections` to rename them
- **Theming** — all colors are CSS variables at the top of `style.css`
