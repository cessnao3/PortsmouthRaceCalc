import enum

# TODO - Convert to SQLite?


class Series:
    def __init__(self, name, qualify_count, fleet, boat_overrides):
        self.name = name
        self.qualify_count = qualify_count
        self.fleet = fleet
        self.races = []
        self.boat_overrides = boat_overrides if boat_overrides is not None else dict()

    def add_race(self, race):
        self.races.append(race)

    def get_all_skippers(self):
        pass


class Race:
    def __init__(self, series, rc, date, wind_bf, notes):
        self.race_times = dict()
        self.series = series
        self.date = date
        self.wind_bf = wind_bf
        self.notes = notes

        for rc_skipper in rc:
            self.add_skipper_time(RaceTime(
                race=self,
                skipper=rc_skipper,
                time_s=RaceTime.RaceFinishOther.RC))

    def add_skipper_time(self, race_time):
        skip_id = race_time.skipper.identifier

        if skip_id in self.race_times:
            raise ValueError(
                'Cannot add duplicate {:s} race time for {:s}'.format(
                    self.series.name,
                    skip_id))
        else:
            self.race_times[race_time.skipper.identifier] = race_time

    def get_race_table(self):
        str_list = []

        str_list.append(' Wind: {:d} (BFT)'.format(self.wind_bf))
        str_list.append('   RC: {:s}'.format(', '.join([s.identifier for s in self.rc_skippers()])))
        str_list.append(' Date: {:s}'.format(self.date))
        str_list.append('Notes: {:s}'.format(self.notes))
        str_list.append('                    a_time                        c_time')
        str_list.append('       Name   Boat   mm:ss   sec  /   hc  =c_sec   mm:ss  Rank')
        str_list.append('-----------   ----   -----   -------------------   -----  ----')

        place = 1

        race_time_list = [self.race_times[r] for r in self.race_times if self.race_times[r].finished()]
        race_time_list.sort(key=lambda x: x.corrected_time_s)

        for race_time in race_time_list:
            str_list.append('{:11s} {:6s}   {:5s}   {:4d} / {:0.03f} = {:4d}   {:5s}  {:2d}'.format(
                race_time.skipper.identifier,
                race_time.boat.code,
                race_time.format_time(race_time.time_s),
                int(race_time.time_s),
                race_time.boat.dpn_for_beaufort(self.wind_bf) / 100.0,
                round(race_time.corrected_time_s),
                race_time.format_time(race_time.corrected_time_s),
                place))
            place += 1

        if len([self.race_times[r] for r in self.race_times if self.race_times[r].has_other_result()]) > 0:
            raise ValueError('Warning: No printing for other race results')

        return '\n'.join(str_list)

    def rc_skippers(self):
        return [self.race_times[r].skipper for r in self.race_times if self.race_times[r].is_rc()]

    def get_points_for_skipper(self, skipper):
        pass


class RaceTime:
    class RaceFinishOther(enum.Enum):
        RC = 0
        DNF = 1
        DQ = 2

    def __init__(self, race, skipper, time_s=None):
        self.race = race
        self.skipper = skipper

        if type(time_s) is not int and type(time_s) is not self.RaceFinishOther:
            raise TypeError('Race Time must be an int or a race finish value')

        self.time_s = time_s
        boat_id = self.skipper.default_boat_code
        if skipper.identifier in race.series.boat_overrides:
            boat_id = race.series.boat_overrides[skipper.identifier]
        self.boat = race.series.fleet.get_boat(boat_id)

    def finished(self):
        return type(self.time_s) is not self.RaceFinishOther

    def has_other_result(self):
        return not self.finished() and self.time_s != self.RaceFinishOther.RC

    def is_rc(self):
        return not self.finished and self.time_s == self.RaceFinishOther.RC

    @property
    def corrected_time_s(self):
        return self.time_s * 100.0 / self.boat.dpn_for_beaufort(self.race.wind_bf)

    @staticmethod
    def format_time(time_s):
        s_val = time_s % 60
        time_c = int((time_s - s_val) / 60)
        m_val = time_c
        return '{:02d}:{:02d}'.format(m_val, round(s_val))

