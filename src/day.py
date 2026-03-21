from datetime import date

class Day:
    def __init__(self, day_number, rooms, day_date=None):
        self.day = day_number  # 1-7 for Mon-Sun
        self.rooms = rooms  # Each day has its own copy of rooms
        self.date = day_date  # The actual date of this day