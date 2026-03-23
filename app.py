from datetime import date, datetime, timedelta

from flask import Flask, jsonify, render_template, request

from scheduler import Scheduler

def get_display_sets(current_day, scheduler, ref_date):
    """Return three sets of (room_name, task_name) tuples based on ref_date.

    Uses the database to efficiently find the last completion for each task.

    - display_done : done on current_day
    - locked       : done on a past day and still within its repeat interval
    - overdue      : last completion was >= 2 × repeat days ago (not done in last interval)

    Intervals are measured in days from the last completion date.
    When a new interval begins (days_since >= repeat), the task becomes unlocked/pending again.
    """
    ref = ref_date if isinstance(ref_date, date) else ref_date.date()
    display_done = set()
    locked = set()
    overdue = set()

    # Get the earliest date from database for overdue calculations
    earliest_date, _ = scheduler._database.get_date_range()
    if earliest_date is None:
        earliest_date = ref
    
    # Process tasks from current day
    for room_name, room in current_day.rooms.items():
        for task in room.tasks:
            is_current_day = False

            # Check if task is completed on current day
            if task.doneBy and task.doneWhen:
                done_date = task.doneWhen.date() if hasattr(task.doneWhen, 'date') else task.doneWhen
                if done_date == ref:
                    is_current_day = True

            # Get last completion from database (on or before ref_date)
            last_completion = scheduler.get_last_completion(room_name, task.name, ref)
            
            if last_completion is None and not is_current_day:
                # Task never completed - check if it should be overdue
                days_since_start = (ref - earliest_date).days
                if days_since_start >= task.repeat * 2:
                    overdue.add((room_name, task.name))
                continue

            # Determine the last done time
            if is_current_day:
                last_done = task.doneWhen
                last_done_date = task.doneWhen.date() if hasattr(task.doneWhen, 'date') else task.doneWhen
            elif last_completion:
                last_done = last_completion['done_when']
                last_done_date = last_completion['day_date']
            else:
                continue

            days_since = (ref - last_done_date).days
            
            # Day-based interval logic:
            # - Within interval (days_since < repeat - 1): locked or display_done
            # - New interval started (repeat - 1 <= days_since < 2×repeat - 1): unlocked (pending)
            # - Not done in last interval (days_since >= 2×repeat - 1): overdue
            
            # Debug logging
            from src.setup.config import Config
            if Config().get_debug_mode():
                print(f"[DEBUG] Task '{task.name}' in '{room_name}': days_since={days_since}, repeat={task.repeat}, is_current_day={is_current_day}, ref={ref}, last_done_date={last_done_date}")
            
            if days_since < task.repeat - 1:
                # If done on current day, always show as display_done
                if is_current_day:
                    display_done.add((room_name, task.name))
                else:
                    # Still within the interval, keep it locked
                    locked.add((room_name, task.name))
            elif days_since >= task.repeat * 2 - 1:
                # At least one full interval has passed without completion → overdue
                overdue.add((room_name, task.name))
            # else: task.repeat <= days_since < task.repeat * 2
            #       New interval has started, task is due but not yet overdue → plain pending

    return display_done, locked, overdue


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
        "date_only_format": "%d.%m.%Y",
        "nav_prev": "← Vorherige Woche",
        "nav_next": "Nächste Woche →",
        "nav_next_current": "Aktuelle Woche →",
        "nav_to_current": "Zur aktuellen Woche",
        "readonly_notice": "Vergangene Woche — Nur Ansicht",
        "readonly_past_day": "Vergangener Tag",
        "readonly_view_only": "Nur Ansicht",
        "goto_today": "Zu Heute",
        "overdue_label": "Überfällig",
        "locked_label": "Kürzlich erledigt",
        "progress_label": "erledigt",
        "total_progress_label": "Aufgaben diese Woche erledigt",
        "day_names": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
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
        "date_only_format": "%m/%d/%Y",
        "nav_prev": "← Previous Week",
        "nav_next": "Next Week →",
        "nav_next_current": "Current Week →",
        "nav_to_current": "Go to current week",
        "readonly_notice": "Past Week — Read Only",
        "readonly_past_day": "Past Day",
        "readonly_view_only": "View Only",
        "goto_today": "Go to Today",
        "overdue_label": "Overdue",
        "locked_label": "Recently done",
        "progress_label": "done",
        "total_progress_label": "tasks done this week",
        "day_names": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    },
}


def create_app(scheduler):
    app = Flask(__name__, template_folder="frontend", static_folder="frontend")

    @app.after_request
    def add_header(response):
        """Add cache control headers to prevent browser caching."""
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route("/")
    def home():
        """Show today's tasks by default."""
        today = datetime.now().date()
        return show_day(today, is_current=True)
    
    @app.route("/day/<int:year>/<int:month>/<int:day_of_month>")
    def day_view(year, month, day_of_month):
        """Show a specific day's tasks."""
        try:
            target_date = date(year, month, day_of_month)
        except ValueError:
            return "Invalid date", 404
        
        today = datetime.now().date()
        is_current = target_date == today
        return show_day(target_date, is_current=is_current)
    
    def show_day(target_date, is_current=False):
        """Display tasks for a specific day."""
        today = datetime.now().date()
        readonly = target_date < today
        
        # Get the day object for the target date
        current_day = scheduler.get_day(target_date)
        if current_day is None:
            return "Day not found", 404
        
        # Get week info for the target date
        week = scheduler.get_week_for_date(target_date)
        if week is None:
            return "Week not found", 404
        
        # Calculate display sets using database
        display_done, locked, overdue = get_display_sets(current_day, scheduler, target_date)
        
        users = scheduler._config.get_users()
        lang = scheduler._config.get_language_key().value
        t = TRANSLATIONS[lang]
        
        # Calculate week days for navigation
        monday = target_date - timedelta(days=target_date.weekday())
        week_days = [monday + timedelta(days=i) for i in range(7)]
        
        # Check if this is a past week (Sunday of the week is before today)
        sunday = monday + timedelta(days=6)
        is_past_week = sunday < today
        
        # Find previous and next weeks (same weekday)
        prev_week_day_calc = target_date - timedelta(days=7)
        next_week_day = target_date + timedelta(days=7)
        
        # Check if we can navigate to previous week (week must exist in scheduler)
        prev_week = scheduler.get_week_for_date(prev_week_day_calc)
        prev_week_day = prev_week_day_calc if prev_week is not None else None
        
        # Check if we can navigate to next week
        next_week_monday = next_week_day - timedelta(days=next_week_day.weekday())
        can_go_next_week = next_week_monday <= today
        next_is_current_week = next_week_monday <= today <= (next_week_monday + timedelta(days=6))
        
        return render_template(
            "index.html",
            day=current_day,
            week=week,
            users=users,
            lang=lang,
            t=t,
            readonly=readonly,
            overdue=overdue,
            locked=locked,
            display_done=display_done,
            selected_day=target_date,
            today=today,
            week_days=week_days,
            prev_week_day=prev_week_day,
            next_week_day=next_week_day if can_go_next_week else None,
            next_is_current_week=next_is_current_week,
            is_current=is_current,
            is_past_week=is_past_week,
            debug_mode=scheduler.get_debug_mode(),
        )

    @app.route("/week/<int:year>/<int:week_no>")
    def past_week_view(year, week_no):
        """View a past week - shows the Monday of that week."""
        past_weeks = scheduler.get_past_week()
        week = past_weeks.get((year, week_no))
        if not week:
            return "Week not found", 404
        
        # Show the Monday of the past week
        monday = week.days[0]
        if monday.date:
            return show_day(monday.date, is_current=False)
        else:
            return "Week date not found", 404

    @app.route("/api/task/complete", methods=["POST"])
    def complete_task():
        data = request.get_json(silent=True) or {}
        room_name = data.get("room", "").strip()
        task_name = data.get("task", "").strip()
        done_by = data.get("doneBy", "").strip()
        day_date_str = data.get("dayDate")  # Expected format: "YYYY-MM-DD"

        if not room_name or not task_name or not done_by or not day_date_str:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            day_date = datetime.strptime(day_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        day = scheduler.get_day(day_date)
        if not day:
            return jsonify({"error": "Day not found"}), 404
        
        room = day.rooms.get(room_name)
        if not room:
            return jsonify({"error": "Room not found"}), 404

        task = next((t for t in room.tasks if t.name == task_name), None)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        task.doneBy = done_by
        # In debug mode, use the day's date instead of current time
        if scheduler.get_debug_mode():
            task.doneWhen = datetime.combine(day_date, datetime.now().time())
        else:
            task.doneWhen = datetime.now()

        # Save to database
        success = scheduler.save_task_completion(
            room_name, task_name, task.repeat, done_by, task.doneWhen, day_date
        )
        
        if not success:
            return jsonify({"error": "Failed to save to database"}), 500

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
        day_date_str = data.get("dayDate")  # Expected format: "YYYY-MM-DD"

        if not room_name or not task_name or not day_date_str:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            day_date = datetime.strptime(day_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        day = scheduler.get_day(day_date)
        if not day:
            return jsonify({"error": "Day not found"}), 404
        
        room = day.rooms.get(room_name)
        if not room:
            return jsonify({"error": "Room not found"}), 404

        task = next((t for t in room.tasks if t.name == task_name), None)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        task.doneBy = None
        task.doneWhen = None

        # Delete from database
        success = scheduler.delete_task_completion(room_name, task_name, day_date)
        
        if not success:
            return jsonify({"error": "Failed to delete from database"}), 500

        return jsonify({"success": True})

    return app


if __name__ == "__main__":
    scheduler = Scheduler()
    app = create_app(scheduler)
    app.run(debug=True, host="0.0.0.0", port=5000)