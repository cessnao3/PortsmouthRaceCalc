import csv
import enum
import yaml


class Boat:
    table_file_name = 'portsmouth_table_2017.csv'

    class BoatClass(enum.Enum):
        UNKNOWN = 0
        CENTERBOARD = 1
        KEELBOAT = 2

    def __init__(self, name, boat_class, code, dpn_vals):
        self.name = name
        self.boat_class = boat_class
        self.code = code
        self.dpn_vals = dpn_vals

    def dpn_for_beaufort(self, beaufort):
        if type(beaufort) != int:
            raise ValueError('Beaufort number must be of type int')

        if beaufort <= 1:
            dpn_ind = 1
        elif beaufort <= 3:
            dpn_ind = 2
        elif beaufort <= 4:
            dpn_ind = 3
        else:
            dpn_ind = 4

        while self.dpn_vals[dpn_ind] is None and dpn_ind > 0:
            dpn_ind -= 1

        if self.dpn_vals[dpn_ind] is None:
            raise RuntimeError('No DPN provided for code {:s}, index {:d}'.format(self.code, dpn_ind))

        return self.dpn_vals[dpn_ind]

    @staticmethod
    def from_row(row):
        def dpn_to_float(s):
            s_list = list(s)
            if len(s_list) > 0 and s_list[0] in ('(', '['):
                s_list = s_list[1:-1]

            if len(s_list) == 0:
                return None
            else:
                return float(''.join(s_list))

        if row['class'].lower() == 'centerboard':
            boat_class = Boat.BoatClass.CENTERBOARD
        elif row['class'].lower() == 'keelboat':
            boat_class = Boat.BoatClass.KEELBOAT
        else:
            print('Unknown boat class {:s}'.format(row['class']))
            boat_class = Boat.BoatClass.UNKNOWN

        dpn_vals = [dpn_to_float(row['dpn'])]
        dpn_vals += [dpn_to_float(row['dpn{:d}'.format(i + 1)]) for i in range(4)]

        return Boat(
            name=row['boat'],
            boat_class=boat_class,
            code=row['code'].lower(),
            dpn_vals=dpn_vals)

    @staticmethod
    def default():
        return Boat.from_csv_file(Boat.table_file_name)

    @staticmethod
    def from_csv_file(table_file_name):
        boats = dict()

        with open(table_file_name, 'r') as f:
            reader = csv.reader(f)

            header_cols = None

            for row in reader:
                row = [v.strip() for v in row]

                if header_cols is None:
                    header_cols = [v.lower() for v in row]
                    continue

                if len(row) != len(header_cols):
                    print('ERROR! {:s}'.format(', '.join(row)))
                    continue
                else:
                    row_dict = {header_cols[i]: row[i] for i in range(len(header_cols))}

                    b = Boat.from_row(row_dict)

                    if b.dpn_vals[0] is None:
                        print('Skipping {:s} due to no provided DPN values'.format(b.name))
                        continue

                    if b.code in boats:
                        raise ValueError('Boat {:s} already in dictionary'.format(b.code))

                    boats[b.code] = b

        return boats


class Series:
    def __init__(self):
        pass

class Race:
    def __init__(self):
        pass

class Skipper:
    def __init__(self):
        pass

#Ian_O     SF   39:58   2398 / 1.004 = 2388   39:48   5

time = 39*60 + 58
time = 64*60 + 26

time_c = time * 100 / boats['sf'].dpn_for_beaufort(2)
s_val = time_c % 60
time_c = int((time_c - s_val) / 60)
m_val = time_c % 60
time_c = (time_c - m_val) // 60
h_val = time_c

print('Time: {:02d}:{:02d}:{:05.02f}'.format(h_val, m_val, s_val))
