# from sqlalchemy import create_engine, text
# import mysql.connector
# from sqlalchemy_utils import create_database
# import requests
# import xml.etree.ElementTree as ElementTree
#
# ACCESSCODE = "1D593BCBB727A29D"
#
# class Db:
#     def __init__ (self):
#
#         self.__dbconnect()
#         #self.__update_pilot_summary(ACCESSCODE, ACCESSCODE)
#         #self.__update_flight_logs(ACCESSCODE, ACCESSCODE)
#
#     def __dbconnect (self):
#
#         print("Initializing database")
#         self.engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse2", echo=True, future=True)
#         with self.engine.connect() as conn:
#             conn.execute('SELECT 1')
#         try:
#             with self.engine.connect() as conn :
#                 conn.execute('SELECT 1')
#             print('connected to already exsting database')
#
#         except:
#             try:
#                 print(self.engine.url)
#                 create_database(self.engine.url)
#
#                 # db = mysql.connect(
#                 #     host="localhost",
#                 #     user="tree",
#                 #     password="password",
#                 # )
#
#
#                 # with engine.connect() as conn:
#                 #     #conn.execute('commit')
#                 #     print('Database does not exist, connected to mysql')
#                 #     # Check if the table is there
#                 #     err = conn.execute("CREATE DATABASE fse2")
#                 #     print(err)
#                 #     print('created')
#                 #     conn.execute("use fse2")
#                 #     print('using')
#                 #
#                 # engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse2", echo=True, future=True)
#                 # engine.connect()
#                 print('Created database')
#                 # db = mysql.connect(
#                 #     host="localhost",
#                 #     user="tree",
#                 #     password="password",
#                 #     database="fse"
#                 #     )
#                 # cursor = db.cursor()
#                 # cursor = create_pilot_tables(cursor)
#                 # cursor = create_flight_log_table(cursor)
#                 # db.commit()
#
#             except:
#                 print("Unable to connect with mySQL database")
#                 exit()
#
#     def __update_pilot_summary(db, youraccesscode, pilotsaccesscode):
#
#         def get_summary_info(url):
#             resp = requests.get(url)
#             root = ElementTree.fromstring(resp.text)
#             entries = {}
#             entries['name'] = root[0].attrib.get('account')
#             for i in root[0]:
#                 label = i.tag.split('}')[-1].lower()
#                 entries[label] = i.text
#             return entries
#
#         # get info
#         url = f"https://server.fseconomy.net/data?userkey={youraccesscode}&format=xml&query=statistics&search=key&readaccesskey={pilotsaccesscode}"
#         entries = get_summary_info(url)
#
#         # add to pilot db. This will only add something the first time the pilot info is requested.  Subsequent calls will
#         # not insert a row into the pilot db
#
#         sql = f'''INSERT INTO pilot (name, readaccesskey) VALUES ('{entries["name"]}', '{pilotsaccesscode}')'''
#         cursor = db.cursor()
#
#         try:
#             cursor.execute(sql)
#         except mysql.errors.IntegrityError:
#             # do nothing, already in db
#             print(f'Pilot {entries["name"]} already in db')
#
#         # pilot has now been added to db, add summary to stat table.
#         time_split = entries['time_flown'].split(':')
#         sql = f'''INSERT INTO pilot_stat (name, personal_balance, bank_balance, flights, total_miles, time_flown_hr, time_flown_min) \
#     VALUES ('{entries["name"]}','{entries["personal_balance"]}', '{entries["bank_balance"]}', '{entries["flights"]}', '{entries["total_miles"]}', {time_split[0]}, {time_split[-1]})'''
#         cursor.execute(sql)
#
#         db.commit()
#
# #     def __create_pilot_tables (self):
# #         # sql = ("CREATE TABLE pilot (name VARCHAR(255) NOT NULL, "
# #         #        "readaccesskey VARCHAR(255), "
# #         #        "PRIMARY KEY (name))"
# #         #        )
# #         # cursor.execute(sql)
# #         # sql = ("CREATE TABLE pilot_stat (name VARCHAR(255) NOT NULL, "
# #         #        "date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP , "
# #         #        "personal_balance DECIMAL (13,2) NOT NULL DEFAULT 0, "
# #         #        "bank_balance DECIMAL (13,2) NOT NULL DEFAULT 0, "
# #         #        "flights INT NOT NULL DEFAULT 0, "
# #         #        "total_miles INT NOT NULL DEFAULT 0, "
# #         #        "time_flown_hr INT UNSIGNED NOT NULL DEFAULT 0, "
# #         #        "time_flown_min TINYINT UNSIGNED NOT NULL DEFAULT 0, "
# #         #        "PRIMARY KEY (name, date), "
# #         #        "FOREIGN KEY (name) REFERENCES pilot(name) ON DELETE CASCADE)"
# #         #        )
# #         # cursor.execute(sql)
# #         # return cursor
# #
# # def create_flight_log_table (cursor):
# #     sql = ("CREATE TABLE flightlog (Id INT NOT NULL, "
# #            "Type VARCHAR(250) NOT NULL, "
# #            "Time DATETIME NOT NULL, "
# #            "Distance INT NOT NULL, "
# #            "Pilot VARCHAR(250) NOT NULL, "
# #            "SerialNumber INT NOT NULL, "
# #            "Aircraft VARCHAR(250) NOT NULL, "
# #            "MakeModel VARCHAR(250) NOT NULL, "
# #            "FromAirport VARCHAR(40), "
# #            "ToAirport VARCHAR(40), "
# #            "TotalEngineTime TIME NOT NULL, "
# #            "FlightTime TIME NOT NULL, "
# #            "GroupName VARCHAR(255), "
# #            "Income DECIMAL (13,2) NOT NULL, "
# #            "PilotFee DECIMAL (13,2) NOT NULL, "
# #            "CrewCost DECIMAL (13,2) NOT NULL, "
# #            "BookingFee DECIMAL (13,2) NOT NULL, "
# #            "Bonus DECIMAL (13,2) NOT NULL, "
# #            "FuelCost DECIMAL (13,2) NOT NULL, "
# #            "GCF DECIMAL (13,2) NOT NULL, "
# #            "RentalPrice DECIMAL (13, 2), "
# #            "RentalType VARCHAR (255), "
# #            "RentalUnits TIME, "
# #            "RentalCost DECIMAL (13,2), "
# #            "PRIMARY KEY (Id), "
# #            "FOREIGN KEY (Pilot) REFERENCES pilot(name) ON DELETE CASCADE)"
# #            )
# #     cursor.execute(sql)
# #     return cursor
# #
#
#
#
#
#
# # def get_flight_log_info(youraccesscode, pilotaccesscode, lastID):
# #     url =f'https://server.fseconomy.net/data?userkey={youraccesscode}&format=xml&query=flightlogs&search=id&readaccesskey={pilotaccesscode}&fromid={lastID}'
# #     resp = requests.get(url)
# #     root = ElementTree.fromstring(resp.text)
# #     entries = []
# #
# #     for flight in root:
# #         entry = {}
# #         for item in flight:
# #             title = item.tag.split('}')[-1]
# #             if title == 'To':
# #                 title = 'to_airport'
# #             elif title == 'From':
# #                 title = 'from_airport'
# #             elif title == 'GCF':
# #                 title = title.lower()
# #             else:
# #                 # shift to snake_case
# #                 title = re.sub(r'(?<!^)(?=[A-Z])', '_', title).lower()
# #             entry[title] = item.text if item.text else ''
# #
# #         entries.append(entry)
# #
# #     return entries
#
# def update_flight_logs (db, youraccesscode, pilotaccesscode):
#     engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse", echo=True)
#     cursor = db.cursor()
#     #get last entry
#     lastID = 0
#     try:
#         sql = f'''SELECT id FROM flightlog INNER JOIN pilot ON flightlog.pilot = pilot.name WHERE pilot.readaccesskey='{pilotaccesscode}' ORDER BY id DESC LIMIT 1'''
#         print(sql)
#
#         cursor.execute(sql)
#         res = cursor.fetchall()
#         print('res:', res)
#         if res:
#             lastID = res[0]
#
#     except:
#         # lastID already 0
#         pass
#
#     # Get data from FSEconomy in CSV format
#     url = f'https://server.fseconomy.net/data?userkey={youraccesscode}&format=csv&query=flightlogs&search=id&readaccesskey={pilotaccesscode}&fromid={lastID}'
#     csv = requests.get(url);
#     # Import it into a Pandas dataframe. Sets the Id number to be the index
#     df = pd.read_csv(StringIO(csv.text), index_col=0)
#     # Remove unnamed and useless column at the end of the import
#     df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
#
#     # Add to the database.  This also creates the table if needed
#     with engine.connect() as conn:
#         # Check if the table is there
#         try:
#             s = text("SELECT :item FROM flightlog ")
#             conn.execute(s, {"item": 'pilot'})
#             df.to_sql('flightlog', con=engine, if_exists='append', method='multi')
#             # TODO: Set foriegn key relationships for on-delete and on-update
#             # TODO: Set Id to be unique
#
#         except:
#             print("does not exist")
#             df.to_sql('flightlog', con=engine, if_exists='fail', method='multi')