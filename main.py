# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import mysql.connector as mysql
import requests
import xml.etree.ElementTree as ElementTree
import re
import pandas as pd
from io import StringIO

ACCESSCODE = "1D593BCBB727A29D"

def dbconnect ():
    try:
        connect = mysql.connect(
        host="localhost",
        user="tree",
        password="password",
        database="fse"
        )
        return connect
    except:
        try:
            db = mysql.connect(
                host="localhost",
                user="tree",
                password="password",
            )
            cursor = db.cursor()
            cursor.execute('CREATE DATABASE fse')
            cursor.close()
            db = mysql.connect(
                host="localhost",
                user="tree",
                password="password",
                database="fse"
                )
            cursor = db.cursor()
            cursor = create_pilot_tables(cursor)
            cursor = create_flight_log_table(cursor)
            db.commit()
            return (db)

        except:
            print("Unable to connect with mySQL database")
            exit()


def create_pilot_tables (cursor):
    sql = ("CREATE TABLE pilot (name VARCHAR(255) NOT NULL, "
           "readaccesskey VARCHAR(255), "
           "PRIMARY KEY (name))"
           )
    cursor.execute(sql)
    sql = ("CREATE TABLE pilot_stat (name VARCHAR(255) NOT NULL, "
           "date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP , "
           "personal_balance DECIMAL (13,2) NOT NULL DEFAULT 0, "
           "bank_balance DECIMAL (13,2) NOT NULL DEFAULT 0, "
           "flights INT NOT NULL DEFAULT 0, "
           "total_miles INT NOT NULL DEFAULT 0, "
           "time_flown_hr INT UNSIGNED NOT NULL DEFAULT 0, "
           "time_flown_min TINYINT UNSIGNED NOT NULL DEFAULT 0, "
           "PRIMARY KEY (name, date), "
           "FOREIGN KEY (name) REFERENCES pilot(name) ON DELETE CASCADE)"
           )
    cursor.execute(sql)
    return cursor

def create_flight_log_table (cursor):
    sql = ("CREATE TABLE flightlog (Id INT NOT NULL, "
           "Type VARCHAR(250) NOT NULL, "
           "Time DATETIME NOT NULL, "
           "Distance INT NOT NULL, "
           "Pilot VARCHAR(250) NOT NULL, "
           "SerialNumber INT NOT NULL, "
           "Aircraft VARCHAR(250) NOT NULL, "
           "MakeModel VARCHAR(250) NOT NULL, "
           "FromAirport VARCHAR(40), "
           "ToAirport VARCHAR(40), "
           "TotalEngineTime TIME NOT NULL, "
           "FlightTime TIME NOT NULL, "
           "GroupName VARCHAR(255), "
           "Income DECIMAL (13,2) NOT NULL, "
           "PilotFee DECIMAL (13,2) NOT NULL, "
           "CrewCost DECIMAL (13,2) NOT NULL, "
           "BookingFee DECIMAL (13,2) NOT NULL, "
           "Bonus DECIMAL (13,2) NOT NULL, "
           "FuelCost DECIMAL (13,2) NOT NULL, "
           "GCF DECIMAL (13,2) NOT NULL, "
           "RentalPrice DECIMAL (13, 2), "
           "RentalType VARCHAR (255), "
           "RentalUnits TIME, "
           "RentalCost DECIMAL (13,2), "
           "PRIMARY KEY (Id), "
           "FOREIGN KEY (Pilot) REFERENCES pilot(name) ON DELETE CASCADE)"
           )
    cursor.execute(sql)
    return cursor

def get_summary_info(url):
    resp = requests.get(url)
    root = ElementTree.fromstring(resp.text)
    entries = {}
    entries['name'] = root[0].attrib.get('account')
    for i in root[0]:
        label = i.tag.split('}')[-1].lower()
        entries[label] = i.text
    return entries


def update_pilot_summary(db, youraccesscode, pilotsaccesscode):
    # get info
    url = f"https://server.fseconomy.net/data?userkey={youraccesscode}&format=xml&query=statistics&search=key&readaccesskey={pilotsaccesscode}"
    entries = get_summary_info(url)

    # add to pilot db. This will only add something the first time the pilot info is requested.  Subsequent calls will
    # not insert a row into the pilot db

    sql = f'''INSERT INTO pilot (name, readaccesskey) VALUES ('{entries["name"]}', '{pilotsaccesscode}')'''
    cursor = db.cursor()

    try:
        cursor.execute(sql)
    except mysql.errors.IntegrityError:
        # do nothing, already in db
        print("Pilot already in db")

    # pilot has now been added to db, add summary to stat table.
    time_split = entries['time_flown'].split(':')
    sql = f'''INSERT INTO pilot_stat (name, personal_balance, bank_balance, flights, total_miles, time_flown_hr, time_flown_min) \
VALUES ('{entries["name"]}','{entries["personal_balance"]}', '{entries["bank_balance"]}', '{entries["flights"]}', '{entries["total_miles"]}', {time_split[0]}, {time_split[-1]})'''
    cursor.execute(sql)

    db.commit()

def get_flight_log_info(youraccesscode, pilotaccesscode, lastID):
    url =f'https://server.fseconomy.net/data?userkey={youraccesscode}&format=xml&query=flightlogs&search=id&readaccesskey={pilotaccesscode}&fromid={lastID}'
    resp = requests.get(url)
    root = ElementTree.fromstring(resp.text)
    entries = []

    for flight in root:
        entry = {}
        for item in flight:
            title = item.tag.split('}')[-1]
            if title == 'To':
                title = 'to_airport'
            elif title == 'From':
                title = 'from_airport'
            elif title == 'GCF':
                title = title.lower()
            else:
                # shift to snake_case
                title = re.sub(r'(?<!^)(?=[A-Z])', '_', title).lower()
            entry[title] = item.text if item.text else ''

        entries.append(entry)

    return entries

def update_flight_logs (db, youraccesscode, pilotaccesscode):
    cursor = db.cursor()
    #get last entry
    sql = f'''SELECT id FROM flightlog INNER JOIN pilot ON flightlog.pilot = pilot.name WHERE pilot.readaccesskey="{pilotaccesscode} ORDER BY id DESC LIMIT 1"'''

    cursor.execute(sql)
    res = cursor.fetchall()
    lastID = 0
    if res:
        lastID = res.id
    print('res:', res)

#     # get all flight logs from the last on in the database
#     entries = get_flight_log_info(youraccesscode, pilotaccesscode, lastID)
#     for entry in entries:
#         sql = f'''INSERT INTO flightlog (id, type, time, distance, pilot, serial_number, aircraft, make_model, \
# from_airport, to_airport, total_engine_time, flight_time, group_name, income, pilot_fee, crew_cost, booking_fee, bonus, fuel_cost,\
# gcf, rental_price, rental_type, rental_units, rental_cost) VALUES ('{entry["id"]}',\
# '{entry["type"]}', '{entry["time"]}', '{entry["distance"]}', '{entry["pilot"]}', '{entry["serial_number"]}', \
# '{entry["aircraft"]}', '{entry["make_model"]}', '{entry["from_airport"]}', '{entry["to_airport"]}', '{entry["total_engine_time"]}', \
# '{entry["flight_time"]}', '{entry["group_name"]}', '{entry["income"]}', '{entry["pilot_fee"]}', '{entry["crew_cost"]}', '{entry["booking_fee"]}',\
# '{entry["bonus"]}', '{entry["fuel_cost"]}', '{entry["gcf"]}', '{entry["rental_price"]}', '{entry["rental_type"]}', '{entry["rental_units"]}', \
# '{entry["rental_cost"]}') '''
#         print(sql)
#         cursor.execute(sql)
    url = f'https://server.fseconomy.net/data?userkey={youraccesscode}&format=csv&query=flightlogs&search=id&readaccesskey={pilotaccesscode}&fromid={lastID}'
    csv = requests.get(url);
    df = pd.read_csv(StringIO(csv.text))
    df.rename(columns={"To": "ToAirport", "From" : "FromAirport"})
    for row in df.itertuples():
        sql = pd.to_sql(row)
        print(sql)


    db.commit()


def main():

    db = dbconnect()
    print("DB: ", db)
    #update_pilot_summary(db, ACCESSCODE, ACCESSCODE)
    update_flight_logs(db, ACCESSCODE, ACCESSCODE)


if __name__ == '__main__':
    main()


