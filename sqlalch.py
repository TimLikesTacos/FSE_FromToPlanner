import csv

from sqlalchemy import create_engine, Column, DateTime, Float, Integer, TIMESTAMP, String, DECIMAL, VARCHAR, ForeignKey, \
    PrimaryKeyConstraint, TIME, select, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func, text
from sqlalchemy.exc import IntegrityError as IntegrityError
import requests
import re
from csv import DictReader
import concurrent.futures
from io import StringIO
import pandas as pd
import math
import xml.etree.ElementTree as ElementTree
from time import sleep
from os import cpu_count

Base = declarative_base()

# MAX_DISTANCE_FOR_CALCS = 500; # nautical miles
#
# def chunked_calc_distance_bearing(port1, chunk):
#     values = []
#     for port2 in chunk:
#         distance, bearing = calc_distance_bearing(port1, port2)
#         if distance < MAX_DISTANCE_FOR_CALCS:
#             values.append(AirportDistance(port1.icao, port2.icao, distance, bearing))
#
#     return values
#
#
# def calc_distance_bearing(port1, port2):
#     if port1 == port2:
#         return 0, 0
#     # Calculate distance in nautical miles using great circles, or the Haversine equation.
#
#     R = 3440;
#     phi1 = port1.lat * math.pi / 180
#     phi2 = port2.lat * math.pi / 180
#     deltaphi = (port2.lat - port1.lat) * math.pi / 180
#     deltalambda = (port2.lon - port1.lon) * math.pi / 180
#
#     a = math.sin(deltaphi / 2) * math.sin(deltaphi / 2) + math.cos(phi1) * math.cos(phi2) * \
#         math.sin(deltalambda / 2) * math.sin(deltalambda / 2)
#     d = 2 * R * math.asin(math.sqrt(a))
#
#     # Calculate bearing from _initial_ location, port1
#     y = math.sin(deltalambda) * math.cos(phi2);
#     x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(deltalambda);
#     theta = math.atan2(y, x);
#     brng = (theta * 180 / math.pi + 360) % 360; # in degrees
#     return d, brng

def init (db):
    engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse2")
    Base.metadata.create_all(engine)
    return engine

class Db:


    def __init__(self):
        self.engine = init(self)
        session = sessionmaker(bind=self.engine)
        self.session = session()
        self.base = declarative_base()
        self.base.metadata.create_all(self.engine)

        ## The following section is for One-Time-Only creation of database
        # Create airport database if needed
        if not self.session.query(Airport).first():
            print("Importing airports from local csv file")
            self.__OTO_import_airports()

            print("Airport import complete")

        else:
            print("Airport tables already exist")


    def __OTO_import_airports(self):

        df = pd.read_csv("./icaodata.csv")
        # Replace 'nan' with None
        df = df.where(df.notnull(), None)

        for item in df.iterrows():
            airport = Airport(data=item)
            self.session.add(airport)

        self.session.commit()



    # def __OTO_calculate_airport_distances(self):
    #
    #
    #     with self.engine.connect() as conn:
    #         stmt = select(Airport)
    #         airports = conn.execute(stmt).fetchall()
    #
    #     # For each airport, find the distance and bearing to each other airport
    #     count = 0;
    #     MAX_WORKERS = cpu_count() - 1
    #
    #     # airports = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    #     chunk_size = math.ceil(len(airports) / MAX_WORKERS)
    #     executor = concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS)
    #
    #     for a in airports:
    #         futures = []
    #         for i in range(MAX_WORKERS):
    #             chunk = airports[(i * chunk_size): ((i + 1) * chunk_size)]
    #             futures.append(executor.submit(chunked_calc_distance_bearing, a, chunk))
    #
    #         for chunk in concurrent.futures.as_completed(futures):
    #             results = chunk.result()
    #             if len(results) > 0:
    #                 self.session.add_all(results)
    #
    #         self.session.commit()

        # for port1 in airports:
        #     count += 1
        #     futures = [None] * len(airports)
        #     inside_count = 0
        #     for port2 in airports:
        #         args = [port1, port2, self.session]
        #         futures[inside_count] = executor.map(calc_and_add(port1, port2), airports, chunksize=10)
        #         inside_count += 1
        #     if count % 10 == 0:
        #         print(count)
        #     concurrent.futures.wait(futures)
        #     self.session.commit()



        # for port1 in airports:
        #     count += 1
        #
        #
        #
        #     # for port2 in airports:
        #     #     if port1 == port2:
        #     #         continue
        #     #
        #     #     (distance, bearing) = calculate_distance(port1, port2)
        #     #     if distance < self.MAX_DISTANCE_FOR_CALCS:
        #     #         the_vector = AirportDistance(port1.icao, port2.icao, distance, bearing)
        #     #         self.session.add(the_vector)
        #
        #     self.session.commit()
        #     if count % 10 == 0:
        #         print(count)








def hhmm_to_dec(value):
    time = value.split(':')
    value = float(time[0]) + float(time[1]) / 60
    return value

class Pilot(Base):
    __tablename__ = 'pilot'

    name = Column(VARCHAR(250), primary_key=True)
    readaccesskey = Column(VARCHAR(250))

    def __init__ (self, name, accesskey):
        self.name = name
        self.readaccesskey = accesskey

class PilotStat(Base):
    __tablename__ = 'pilot_stat'

    name = Column(VARCHAR(250), ForeignKey('pilot.name', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    date = Column(TIMESTAMP, server_default=func.now(), primary_key=True)
    personal_balance = Column(DECIMAL(13,2), default=0, nullable=False)
    bank_balance = Column(DECIMAL(13, 2), default=0, nullable=False)
    flights = Column(Integer, default=0, nullable=False)
    total_miles = Column(Integer, default=0, nullable=False)
    time_flown = Column(DECIMAL(13,2), default=0, nullable=False)

    def __init__ (self, **kwargs):

        for key, value in kwargs['entries'].items():
            # convert time flown to decimal
            if key == "time_flown":
                time = value.split(':')
                value = float(time[0]) + float(time[1]) / 60
            setattr(self, key, value)

class Airport(Base):
    __tablename__ = 'airport'

    icao = Column(String(5), primary_key=True)
    lat = Column(Float)
    lon = Column(Float)
    type = Column(String(40))
    size = Column(Integer)
    name = Column(String(100))
    city = Column(String(40))
    state = Column(String(40))
    country = Column(String(40))

    def __init__(self, **kwargs):

        series = kwargs['data'][1]
        for key, value in series.items():
            setattr(self, key, value)



class FlightLog(Base):
    __tablename__ = 'flightlog'

    id = Column(Integer, primary_key=True, autoincrement=False)
    type = Column(VARCHAR(250), nullable=False)
    time = Column(TIME, nullable=False)
    distance = Column(Integer, nullable=False)
    pilot = Column(VARCHAR(250), ForeignKey('pilot.name'), nullable=False)
    serial_number = Column(Integer, nullable=False)
    aircraft = Column(VARCHAR(250), nullable=False)
    make_model = Column(VARCHAR(250), nullable=False)
    to_airport = Column(VARCHAR(40))
    from_airport = Column(VARCHAR(40))
    total_engine_time = Column(DECIMAL(13,2), nullable=False)
    flight_time = Column(DECIMAL(13,2), nullable=False)
    group_name = Column(VARCHAR(250))
    income = Column(DECIMAL(13,2), nullable=False)
    pilotfee = Column (DECIMAL(13,2), nullable=False)
    crew_cost = Column (DECIMAL(13,2), nullable=False)
    booking_fee = Column(DECIMAL(13,2), nullable=False)
    bonus = Column(DECIMAL(13,2), nullable=False)
    fuel_cost = Column(DECIMAL(13,2), nullable=False)
    gcf = Column(DECIMAL(13,2), nullable=False)
    rental_price = Column(DECIMAL(13,2))
    rental_type = Column(VARCHAR(250))
    rental_units = Column(TIME)
    rental_cost = Column(DECIMAL(13,2))

    def __init__ (self, inputs):
        self.id = inputs[0]
        self.type = inputs[1]
        self.time = inputs[2];
        self.distance = inputs[3]
        self.pilot = inputs[4]
        self.serial_number = inputs[5]
        self.aircraft = inputs[6]
        self.make_model = inputs[7]
        self.from_airport = inputs[8]
        self.to_airport = inputs[9]
        self.total_engine_time = hhmm_to_dec(inputs[10])
        self.flight_time = hhmm_to_dec(inputs[11])
        self.group_name = inputs[12]
        self.income = inputs[13]
        self.pilotfee = inputs[14]
        self.crew_cost = inputs[15]
        self.booking_fee = inputs[16]
        self.bonus = inputs[17]
        self.fuel_cost = inputs[18]
        self.gcf = inputs[19]
        self.rental_price = inputs[20]
        self.rental_type = inputs[21]
        self.rental_units = inputs[22]
        self.rental_cost = inputs[23]



def get_flight_log_info(youraccesscode, pilotaccesscode, lastID):
    engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse2", echo=True, echo_pool=True)
    Session = sessionmaker(bind=engine)
    url =f'https://server.fseconomy.net/data?userkey={youraccesscode}&format=csv&query=flightlogs&search=id&readaccesskey={pilotaccesscode}&fromid={lastID}'

    csv = requests.get(url);
    # Import it into a Pandas dataframe. Sets the Id number to be the index
    df = pd.read_csv(StringIO(csv.text))
    # Remove unnamed and useless column at the end of the import
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # Replace NaN with None
    df = df.replace({math.nan: None})

    session = Session()
    for item in df.iterrows():
        data = item[1].array

        flight = FlightLog(data)
        session.add(flight)

    session.commit()

def update_pilot_summary(youraccesscode, pilotsaccesscode):


    url = f"https://server.fseconomy.net/data?userkey={youraccesscode}&format=xml&query=statistics&search=key&readaccesskey={pilotsaccesscode}"
    resp = requests.get(url)
    root = ElementTree.fromstring(resp.text)
    entries = {}
    entries['name'] = root[0].attrib.get('account')
    for i in root[0]:
        label = i.tag.split('}')[-1].lower()
        entries[label] = i.text

    stat = PilotStat(entries=entries)

    engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse2")
    Session = sessionmaker(bind=engine)
    session = Session()

    exists = session.query(Pilot.name).filter_by(name=entries['name']).first() is not None
    if not exists:
        pilot = Pilot(entries['name'], pilotsaccesscode)
        session.add(pilot)

    session.add(stat)
    session.commit()



def create_db():

    engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse2")
    session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
