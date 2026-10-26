# Attendance Management System

A small Flask web app for managing student attendance. Students are added by roll number, attendance is marked per date, and the whole thing is stored in a plain JSON file — no database, no setup beyond installing Flask.

## Features

- Add and remove students
- Mark Present / Absent for any date, with "All present" / "All absent" shortcuts
- Edit a previously saved date without losing history
- Live summary cards: total students, present, absent, class average
- Automatic Good / Low badge per student (below 75% is marked Low)
- One-click CSV export that opens directly in Excel

## Requirements

- Python 3.7 or newer (3.10+ recommended)
- The packages listed below

## Packages to install

This project depends on **one third-party package**:

| Package | Why it is needed |
| ------- | ---------------- |
| `flask` | Serves the web page and handles the forms (`/add`, `/mark`, `/delete`, `/export`) |

Everything else used by `App.py` (`csv`, `io`, `json`, `os`, `datetime`) ships with Python itself, so nothing else needs to be installed.

Install it with:

```bash
pip install flask
```

Optionally, if you prefer an isolated environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install flask
```

## How to run

1. Open a terminal in this folder.
2. Install Flask (see above).
3. Start the server:

   ```bash
   python App.py
   ```

4. Open <http://127.0.0.1:5000> in your browser.

The server runs in debug mode, so it reloads automatically whenever you edit `App.py`.

## Files

| File | Purpose |
| ---- | ------- |
| `App.py` | The whole application: Flask routes, JSON helpers, and the HTML/CSS page |
| `attendance_data.json` | Your saved data — students and the attendance recorded for each date |
| `README.md` | This file |

### Data format

`attendance_data.json` holds two keys:

```json
{
    "students": {
        "26MCC20030": "Kartik Sharma"
    },
    "attendance": {
        "2026-10-26": {
            "26MCC20030": "P"
        }
    }
}
```

`students` maps roll number to name. `attendance` maps each date to a per-roll status of `"P"` (present) or `"A"` (absent). The file is created automatically on first save if it does not exist.

## How it works

- `load_data()` / `save_data()` read and write the JSON file.
- `get_percentage(data, roll)` counts present days for a student and returns the percentage.
- The date picker on the page reloads the report for whichever date you select, so you can jump back and edit any day's record.

## Notes

- The data file is plain JSON, so you can read or edit it by hand — handy for backups.
- Percentage is rounded to one decimal place.
- Students with no recorded days show a "No data" badge instead of 0%.

## Troubleshooting

**`ModuleNotFoundError: No module named 'flask'`**
Flask is not installed in the interpreter you are running with. Run `pip install flask`, or `python -m pip install flask` if you have multiple Python versions installed.

**Port 5000 already in use**
Something else is already running on that port. Stop it, or change the last line of `App.py` to `app.run(debug=True, port=5001)`.

**Data looks stale**
The server writes `attendance_data.json` in the folder you ran `python App.py` from, so always start it from the project directory.
