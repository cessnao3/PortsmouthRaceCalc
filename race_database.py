
# TODO - Convert to SQLite?

class Series:
    def __init__(self, name):
        self.races = []

    def add_race(self, race):
        self.races.append(race)

    def get_all_skippers(self):
        pass

class Race:
    def __init__(self, rc, date, wind):
        pass

    def get_points_for_skipper(self, skipper):
        pass

class RaceTime:
    def __init__(self, skipper, time_s, boat_override=None):
        pass
