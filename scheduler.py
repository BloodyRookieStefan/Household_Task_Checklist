import src
import copy
import random

from datetime import datetime, timedelta

class Scheduler:
    def __init__(self) -> None:
        self._config = src.setup.Config()
        self._config.load()
        self._pastWeeks = dict()
        self._currentWeek = None

        self.create_new_week()

        if self._config.get_debug_mode():
            self.create_debug_weeks()

    def get_current_week(self) -> src.week.Week:
        ''' Get the current week. '''
        return self._currentWeek
    
    def get_past_week(self) -> dict:
        ''' Get the past weeks as a dictionary with the key being a tuple of (year, weekNumber) and the value being the Week object. '''
        return self._pastWeeks

    def create_new_week(self) -> None:
        ''' Create a new week and store the current week in the past weeks if it exists. '''
        if self._currentWeek is not None:
            key = (self._currentWeek.year, self._currentWeek.weekNumber)
            self._pastWeeks[key] = self._currentWeek
            if len(self._pastWeeks) > 40:       # Store max 40 weeks
                self._pastWeeks.pop(min(self._pastWeeks.keys()))
        iso = datetime.now().isocalendar()
        self._currentWeek = src.week.Week(iso.week, iso.year, self._config.get_rooms())


    def create_debug_weeks(self):
        ''' Create 5 debug weeks in the past with randomly completed tasks. '''
        users = self._config.get_users()
        for i in range(1, 6):
            past_date = datetime.now() - timedelta(weeks=i)
            past_iso = past_date.isocalendar()

            rooms_copy = copy.deepcopy(self._config.get_rooms())
            week = src.week.Week(past_iso.week, past_iso.year, rooms_copy)

            monday = past_date - timedelta(days=past_date.weekday())
            for room in week.rooms.values():
                for task in room.tasks:
                    if random.random() < 0.7:  # 70 % chance the task was completed
                        done_day = monday + timedelta(days=random.randint(0, 6))
                        task.doneBy = random.choice(users)
                        task.doneWhen = done_day.replace(
                            hour=random.randint(8, 20),
                            minute=random.randint(0, 59),
                            second=0,
                            microsecond=0,
                        )

            key = (week.year, week.weekNumber)
            self._pastWeeks[key] = week
