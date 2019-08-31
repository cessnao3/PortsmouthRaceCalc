import boat_database as boat_db

boats = boat_db.BoatType.from_csv_file('portsmouth_table_2017.csv')

# Ian_O     SF   39:58   2398 / 1.004 = 2388   39:48   5

time = 39*60 + 58
time = 64*60 + 26

time_c = time * 100 / boats['sf'].dpn_for_beaufort(2)
s_val = time_c % 60
time_c = int((time_c - s_val) / 60)
m_val = time_c % 60
time_c = (time_c - m_val) // 60
h_val = time_c

print('Time: {:02d}:{:02d}:{:05.02f}'.format(h_val, m_val, s_val))
