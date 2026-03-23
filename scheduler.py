import src
import copy

from datetime import datetime, timedelta

class Scheduler:
    def __init__(self) -> None:
        self._config = src.setup.Config()
        self._config.load()
        self._pastWeeks = dict()
        self._currentWeek = None

        if self._config.get_debug_mode():
            self.create_debug_weeks()
    
    def get_debug_mode(self) -> bool:
        ''' Get the debug mode status. '''
        return self._config.get_debug_mode()

    def _check_and_update_week(self) -> None:
        ''' Check if the current week is still valid and create a new week if needed. '''
        if self._currentWeek is None:
            self.create_new_week()
            return
        
        iso = datetime.now().isocalendar()
        # If we're in a different week, create a new week
        if iso.week != self._currentWeek.weekNumber or iso.year != self._currentWeek.year:
            self.create_new_week()

    def get_current_week(self) -> src.week.Week:
        ''' Get the current week. '''
        self._check_and_update_week()
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
        monday = datetime.now().date() - timedelta(days=datetime.now().weekday())
        self._currentWeek = src.week.Week(iso.week, iso.year, self._config.get_rooms(), monday)
    
    def get_day(self, target_date):
        """Get the Day object for a specific date."""
        self._check_and_update_week()
        iso = target_date.isocalendar()
        
        # Check if the date is in the current week
        if iso.year == self._currentWeek.year and iso.week == self._currentWeek.weekNumber:
            day_index = target_date.weekday()  # 0=Monday, 6=Sunday
            return self._currentWeek.days[day_index]
        
        # Check if the date is in a past week
        week_key = (iso.year, iso.week)
        if week_key in self._pastWeeks:
            past_week = self._pastWeeks[week_key]
            day_index = target_date.weekday()
            return past_week.days[day_index]
        
        return None
    
    def get_week_for_date(self, target_date):
        self._check_and_update_week()
        """Get the Week object for a specific date."""
        iso = target_date.isocalendar()
        
        # Check if the date is in the current week
        if iso.year == self._currentWeek.year and iso.week == self._currentWeek.weekNumber:
            return self._currentWeek
        
        # Check if the date is in a past week
        week_key = (iso.year, iso.week)
        if week_key in self._pastWeeks:
            return self._pastWeeks[week_key]
        
        return None


    def create_debug_weeks(self):
        ''' Create 5 debug weeks in the past for testing purposes. '''
        for i in range(1, 6):
            past_date = datetime.now() - timedelta(weeks=i)
            past_iso = past_date.isocalendar()

            monday = (past_date - timedelta(days=past_date.weekday())).date()
            week = src.week.Week(past_iso.week, past_iso.year, self._config.get_rooms(), monday)

            key = (week.year, week.weekNumber)
            self._pastWeeks[key] = week
