from datetime import date, timedelta
import copy
from .day import Day

class Week:
    def __init__(self, weekNumber, year, rooms, start_date=None):
        self.weekNumber = weekNumber
        self.days = list()  # Days of the week (1=Monday, 7=Sunday)
        self.year = year
        self.rooms = rooms  # Keep for backward compatibility
        
        # Calculate the Monday of this week if not provided
        if start_date is None:
            # Approximate the Monday of the week
            from datetime import datetime
            now = datetime.now()
            iso = now.isocalendar()
            if iso.week == weekNumber and iso.year == year:
                monday = now.date() - timedelta(days=now.weekday())
            else:
                # For past weeks, calculate from current week
                current_monday = now.date() - timedelta(days=now.weekday())
                week_diff = (year - iso.year) * 52 + (weekNumber - iso.week)
                monday = current_monday + timedelta(weeks=week_diff)
        else:
            # Ensure start_date is a date object, not datetime
            monday = start_date.date() if hasattr(start_date, 'date') else start_date

        # Create 7 days, each with its own copy of rooms and tasks
        for i in range(1, 8):
            day_date = monday + timedelta(days=i-1)
            rooms_copy = copy.deepcopy(rooms)
            self.days.append(Day(i, rooms_copy, day_date))