import math
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request

from scheduler import Scheduler

def get_overdue_set(current_week, past_weeks):
    """Return set of (room_name, task_name) that are overdue in the current week.

    A task is overdue for a given room when more than one full repeat-cycle
    (measured in whole calendar weeks) has elapsed since it was last done there.
    Example: repeat=7 → due every week → overdue if not done for 2+ weeks.
    If it was done in the immediately preceding cycle it is NOT overdue.
    """
    now = datetime.now()
    overdue = set()
    now_monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    for room_name, room in current_week.rooms.items():
        for task in room.tasks:
            if task.doneBy:
                continue
            last_done = None
            for pw in past_weeks.values():
                past_room = pw.rooms.get(room_name)
                if not past_room:
                    continue
                past_task = next((t for t in past_room.tasks if t.name == task.name), None)
                if past_task and past_task.doneWhen:
                    if last_done is None or past_task.doneWhen > last_done:
                        last_done = past_task.doneWhen
            if last_done is not None:
                weeks_required = math.ceil(task.repeat / 7)
                last_done_monday = (last_done - timedelta(days=last_done.weekday())).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                weeks_elapsed = (now_monday - last_done_monday).days // 7
                if weeks_elapsed > weeks_required:
                    overdue.add((room_name, task.name))
    return overdue


def get_locked_set(current_week, past_weeks):
    """Return set of (room_name, task_name) where the task was recently completed within its repeat window."""
    now = datetime.now()
    locked = set()
    # Monday of the current ISO week
    now_monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    for room_name, room in current_week.rooms.items():
        for task in room.tasks:
            if task.doneBy:
                continue
            last_done = None
            for pw in past_weeks.values():
                past_room = pw.rooms.get(room_name)
                if not past_room:
                    continue
                past_task = next((t for t in past_room.tasks if t.name == task.name), None)
                if past_task and past_task.doneWhen:
                    if last_done is None or past_task.doneWhen > last_done:
                        last_done = past_task.doneWhen
            if last_done is not None:
                # Compare in whole weeks so that a 7-day task done anywhere in the
                # previous calendar week is available again in the current week.
                weeks_required = math.ceil(task.repeat / 7)
                last_done_monday = (last_done - timedelta(days=last_done.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                weeks_elapsed = (now_monday - last_done_monday).days // 7
                if weeks_elapsed < weeks_required:
                    locked.add((room_name, task.name))
    return locked


TRANSLATIONS = {
    "de": {
        "page_title": "Haushaltsplan",
        "subtitle": "Kalenderwochen-Übersicht",
        "cw": "KW",
        "col_task": "Aufgabe",
        "col_done_by": "Erledigt von",
        "every": "alle",
        "days": "Tage",
        "quick_title": "Schnellaktionen",
        "quick_sub": "– Aufgabe in allen Räumen",
        "weekly": "Wöchentlich",
        "every_cap": "Alle",
        "weeks": "Wochen",
        "all_done_undo": "✓ Alle erledigt — Rückgängig",
        "date_format": "%d.%m.%Y %H:%M",
        "nav_prev": "← Vorherige Woche",
        "nav_next": "Nächste Woche →",
        "nav_next_current": "Aktuelle Woche →",
        "nav_to_current": "Zur aktuellen Woche",
        "readonly_notice": "Vergangene Woche — Nur Ansicht",
        "overdue_label": "Überfällig",
        "locked_label": "Kürzlich erledigt",
        "progress_label": "erledigt",
        "total_progress_label": "Aufgaben diese Woche erledigt",
    },
    "en": {
        "page_title": "Household Plan",
        "subtitle": "Calendar Week Overview",
        "cw": "CW",
        "col_task": "Task",
        "col_done_by": "Done by",
        "every": "every",
        "days": "days",
        "quick_title": "Quick Actions",
        "quick_sub": "– Task in all rooms",
        "weekly": "Weekly",
        "every_cap": "Every",
        "weeks": "weeks",
        "all_done_undo": "✓ All done — Undo",
        "date_format": "%m/%d/%Y %H:%M",
        "nav_prev": "← Previous Week",
        "nav_next": "Next Week →",
        "nav_next_current": "Current Week →",
        "nav_to_current": "Go to current week",
        "readonly_notice": "Past Week — Read Only",
        "overdue_label": "Overdue",
        "locked_label": "Recently done",
        "progress_label": "done",
        "total_progress_label": "tasks done this week",
    },
}


def create_app(scheduler):
    app = Flask(__name__, template_folder="frontend")

    @app.route("/")
    def home():
        week = scheduler.get_current_week()
        past_weeks = scheduler.get_past_week()
        users = scheduler._config.get_users()
        lang = scheduler._config.get_language_key().value
        t = TRANSLATIONS[lang]
        overdue = get_overdue_set(week, past_weeks)
        locked = get_locked_set(week, past_weeks)
        sorted_keys = sorted(past_weeks.keys())
        prev_week = sorted_keys[-1] if sorted_keys else None
        return render_template(
            "index.html",
            week=week, users=users, lang=lang, t=t,
            readonly=False, overdue=overdue, locked=locked,
            prev_week=prev_week, next_week=None, next_is_current=False,
            is_current=True,
        )

    @app.route("/week/<int:year>/<int:week_no>")
    def past_week_view(year, week_no):
        past_weeks = scheduler.get_past_week()
        week = past_weeks.get((year, week_no))
        if not week:
            return "Week not found", 404
        users = scheduler._config.get_users()
        lang = scheduler._config.get_language_key().value
        t = TRANSLATIONS[lang]
        sorted_keys = sorted(past_weeks.keys())
        try:
            idx = sorted_keys.index((year, week_no))
        except ValueError:
            return "Week not found", 404
        prev_week = sorted_keys[idx - 1] if idx > 0 else None
        next_week = sorted_keys[idx + 1] if idx + 1 < len(sorted_keys) else None
        next_is_current = next_week is None
        return render_template(
            "index.html",
            week=week, users=users, lang=lang, t=t,
            readonly=True, overdue=set(), locked=set(),
            prev_week=prev_week, next_week=next_week, next_is_current=next_is_current,
            is_current=False,
        )

    @app.route("/api/task/complete", methods=["POST"])
    def complete_task():
        data = request.get_json(silent=True) or {}
        room_name = data.get("room", "").strip()
        task_name = data.get("task", "").strip()
        done_by = data.get("doneBy", "").strip()

        if not room_name or not task_name or not done_by:
            return jsonify({"error": "Missing required fields"}), 400

        week = scheduler.get_current_week()
        room = week.rooms.get(room_name)
        if not room:
            return jsonify({"error": "Room not found"}), 404

        task = next((t for t in room.tasks if t.name == task_name), None)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        task.doneBy = done_by
        task.doneWhen = datetime.now()

        return jsonify({
            "success": True,
            "doneBy": task.doneBy,
            "doneWhen": task.doneWhen.strftime("%d.%m.%Y %H:%M"),
        })

    @app.route("/api/task/uncomplete", methods=["POST"])
    def uncomplete_task():
        data = request.get_json(silent=True) or {}
        room_name = data.get("room", "").strip()
        task_name = data.get("task", "").strip()

        if not room_name or not task_name:
            return jsonify({"error": "Missing required fields"}), 400

        week = scheduler.get_current_week()
        room = week.rooms.get(room_name)
        if not room:
            return jsonify({"error": "Room not found"}), 404

        task = next((t for t in room.tasks if t.name == task_name), None)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        task.doneBy = None
        task.doneWhen = None

        return jsonify({"success": True})

    return app


if __name__ == "__main__":
    scheduler = Scheduler()
    app = create_app(scheduler)
    app.run(debug=True, host="0.0.0.0", port=5000)