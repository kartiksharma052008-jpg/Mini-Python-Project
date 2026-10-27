"""
Attendance Management System (Web Version)
------------------------------------------
A simple website to manage student attendance.
Everything is saved in a file called attendance_data.json.

Step 1:  pip install flask
Step 2:  python attendance_system.py
Step 3:  open http://127.0.0.1:5000 in your browser
"""

import csv
import io
import json
import os
from datetime import date

from flask import Flask, Response, redirect, render_template_string, request

app = Flask(__name__)

FILE_NAME = "attendance_data.json"
MIN_PERCENT = 75  # students below this percentage are marked "Low"


# ---------- Saving and loading data ----------

def load_data():
    """Read data from the file. If the file does not exist, start empty."""
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    return {"students": {}, "attendance": {}}


def save_data(data):
    """Write data to the file."""
    with open(FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)


def get_percentage(data, roll):
    """Return (present_days, total_days, percentage) for one student."""
    total = 0
    present = 0
    for day_record in data["attendance"].values():
        if roll in day_record:
            total += 1
            if day_record[roll] == "P":
                present += 1

    if total == 0:
        return 0, 0, 0
    return present, total, round(present / total * 100, 1)


def go_home(message="", day=""):
    """Send the user back to the main page (with an optional message)."""
    return redirect("/?msg=" + message + "&date=" + day)


# ---------- Pages ----------

@app.route("/")
def home():
    data = load_data()
    selected_date = request.args.get("date") or str(date.today())
    message = request.args.get("msg", "")
    day_record = data["attendance"].get(selected_date, {})

    # Build the report table (one row per student)
    report = []
    percent_list = []
    for roll, name in data["students"].items():
        present, total, percent = get_percentage(data, roll)
        report.append({
            "roll": roll,
            "name": name,
            "present": present,
            "total": total,
            "percent": percent,
            "today": day_record.get(roll, "P"),  # default choice is Present
        })
        if total > 0:
            percent_list.append(percent)

    # Numbers for the cards at the top
    present_count = list(day_record.values()).count("P")
    absent_count = list(day_record.values()).count("A")
    if percent_list:
        average = round(sum(percent_list) / len(percent_list), 1)
    else:
        average = 0

    return render_template_string(
        PAGE,
        report=report,
        message=message,
        selected_date=selected_date,
        already_marked=(selected_date in data["attendance"]),
        total_students=len(data["students"]),
        present_count=present_count,
        absent_count=absent_count,
        average=average,
        min_percent=MIN_PERCENT,
    )


@app.route("/add", methods=["POST"])
def add_student():
    data = load_data()
    roll = request.form["roll"].strip()
    name = request.form["name"].strip()

    if roll == "" or name == "":
        return go_home("Roll number and name are required.")
    if roll in data["students"]:
        return go_home("That roll number already exists.")

    data["students"][roll] = name
    save_data(data)
    return go_home("Student " + name + " added.")


@app.route("/delete/<roll>", methods=["POST"])
def delete_student(roll):
    data = load_data()
    if roll in data["students"]:
        name = data["students"].pop(roll)

        # also remove this student's attendance records
        for day in data["attendance"]:
            data["attendance"][day].pop(roll, None)

        save_data(data)
        return go_home("Student " + name + " removed.")
    return go_home("Student not found.")


@app.route("/mark", methods=["POST"])
def mark_attendance():
    data = load_data()
    day = request.form["date"]

    # Check the date is valid (like 2026-10-26)
    try:
        date.fromisoformat(day)
    except ValueError:
        return go_home("Please choose a valid date.")

    if not data["students"]:
        return go_home("Add some students first.", day)

    day_record = {}
    for roll in data["students"]:
        day_record[roll] = request.form.get("status_" + roll, "A")

    data["attendance"][day] = day_record
    save_data(data)
    return go_home("Attendance saved for " + day + ".", day)


@app.route("/export")
def export_csv():
    """Download the full report as a CSV file (opens in Excel)."""
    data = load_data()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll No", "Name", "Days Present", "Total Days", "Percentage"])
    for roll, name in data["students"].items():
        present, total, percent = get_percentage(data, roll)
        writer.writerow([roll, name, present, total, percent])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_report.csv"},
    )


# ---------- The web page (HTML + CSS) ----------

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Attendance Management System</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Arial, sans-serif; background: #f3f5f9; margin: 0; color: #1f2937; }
  header { background: #2f4fd8; color: white; padding: 18px 24px; }
  header h1 { margin: 0; font-size: 22px; }
  main { max-width: 1000px; margin: 0 auto; padding: 20px; }

  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin-bottom: 20px; }
  .card, .box { background: white; border-radius: 10px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  .card .label { color: #6b7280; font-size: 13px; }
  .card .num { font-size: 28px; font-weight: bold; margin-top: 4px; }
  .box { margin-bottom: 20px; }
  h2 { margin-top: 0; font-size: 18px; }

  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 9px 8px; border-bottom: 1px solid #e5e7eb; }
  th { color: #6b7280; font-size: 13px; }
  .table-wrap { overflow-x: auto; }

  input[type=text], input[type=date] { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; }
  button, .btn { padding: 8px 14px; border: none; border-radius: 6px; background: #2f4fd8; color: white;
                 cursor: pointer; font-size: 14px; text-decoration: none; display: inline-block; }
  .grey { background: #6b7280; }
  .red { background: #dc2626; padding: 5px 10px; font-size: 12px; }
  .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }

  .bar { background: #e5e7eb; border-radius: 6px; height: 10px; width: 110px; display: inline-block; margin-right: 8px; }
  .bar div { height: 10px; border-radius: 6px; background: #16a34a; }
  .bar div.low { background: #dc2626; }

  .badge { padding: 3px 9px; border-radius: 10px; font-size: 12px; }
  .good { background: #dcfce7; color: #166534; }
  .bad { background: #fee2e2; color: #991b1b; }
  .none { background: #e5e7eb; color: #374151; }

  .msg { background: #e0e7ff; padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; }
  .p-label { color: #166534; margin-right: 12px; }
  .a-label { color: #991b1b; }
  .empty { color: #6b7280; }
</style>
</head>
<body>

<header><h1>Attendance Management System</h1></header>

<main>

  {% if message %}
    <div class="msg">{{ message }}</div>
  {% endif %}

  <!-- Cards -->
  <div class="cards">
    <div class="card"><div class="label">Total students</div><div class="num">{{ total_students }}</div></div>
    <div class="card"><div class="label">Present on {{ selected_date }}</div><div class="num">{{ present_count }}</div></div>
    <div class="card"><div class="label">Absent on {{ selected_date }}</div><div class="num">{{ absent_count }}</div></div>
    <div class="card"><div class="label">Class average</div><div class="num">{{ average }}%</div></div>
  </div>

  <!-- Add student -->
  <div class="box">
    <h2>Add a student</h2>
    <form method="POST" action="/add" class="row">
      <input type="text" name="roll" placeholder="Roll number" required>
      <input type="text" name="name" placeholder="Student name" required>
      <button type="submit">Add student</button>
    </form>
  </div>

  <!-- Mark attendance -->
  <div class="box">
    <h2>Mark attendance</h2>

    {% if report %}
      <div class="row" style="margin-bottom: 12px;">
        <label>Date:</label>
        <input type="date" value="{{ selected_date }}" onchange="location.href='/?date=' + this.value">
        <button type="button" class="grey" onclick="markAll('P')">All present</button>
        <button type="button" class="grey" onclick="markAll('A')">All absent</button>
        {% if already_marked %}<span class="badge good">Already saved - you can edit it</span>{% endif %}
      </div>

      <form method="POST" action="/mark">
        <input type="hidden" name="date" value="{{ selected_date }}">
        <div class="table-wrap">
          <table>
            <tr><th>Roll No</th><th>Name</th><th>Status</th></tr>
            {% for s in report %}
            <tr>
              <td>{{ s.roll }}</td>
              <td>{{ s.name }}</td>
              <td>
                <label class="p-label"><input type="radio" name="status_{{ s.roll }}" value="P" {% if s.today == 'P' %}checked{% endif %}> Present</label>
                <label class="a-label"><input type="radio" name="status_{{ s.roll }}" value="A" {% if s.today == 'A' %}checked{% endif %}> Absent</label>
              </td>
            </tr>
            {% endfor %}
          </table>
        </div>
        <br>
        <button type="submit">Save attendance</button>
      </form>
    {% else %}
      <p class="empty">No students yet. Add a student above to start.</p>
    {% endif %}
  </div>

  <!-- Report -->
  <div class="box">
    <div class="row" style="justify-content: space-between; margin-bottom: 8px;">
      <h2 style="margin: 0;">Attendance report</h2>
      <a class="btn grey" href="/export">Download CSV</a>
    </div>

    {% if report %}
      <div class="table-wrap">
        <table>
          <tr><th>Roll No</th><th>Name</th><th>Present</th><th>Total</th><th>Percentage</th><th>Status</th><th></th></tr>
          {% for s in report %}
          <tr>
            <td>{{ s.roll }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.present }}</td>
            <td>{{ s.total }}</td>
            <td>
              <span class="bar"><div class="{% if s.percent < min_percent %}low{% endif %}" style="width: {{ s.percent }}%"></div></span>{{ s.percent }}%
            </td>
            <td>
              {% if s.total == 0 %}<span class="badge none">No data</span>
              {% elif s.percent < min_percent %}<span class="badge bad">Low</span>
              {% else %}<span class="badge good">Good</span>{% endif %}
            </td>
            <td>
              <form method="POST" action="/delete/{{ s.roll }}" onsubmit="return confirm('Remove {{ s.name }}?')">
                <button type="submit" class="red">Remove</button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </table>
      </div>
      <p class="empty">Students below {{ min_percent }}% are marked Low.</p>
    {% else %}
      <p class="empty">Nothing to show yet.</p>
    {% endif %}
  </div>

</main>

<script>
  // Select Present or Absent for every student at once
  function markAll(value) {
    var buttons = document.querySelectorAll('input[type=radio][value=' + value + ']');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].checked = true;
    }
  }
</script>

</body>
</html>
"""


# ---------- Start the website ----------

if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True)  # debug=True reloads the site when you edit this file