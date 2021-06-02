import csv

from sqlalchemy import create_engine, Column, DateTime, Integer, TIMESTAMP, String, DECIMAL, VARCHAR, ForeignKey, TIME
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func, text
from sqlalchemy.exc import IntegrityError as IntegrityError
import requests
import re
from csv import DictReader
from io import StringIO
import pandas as pd
import math
import xml.etree.ElementTree as ElementTree

Base = declarative_base();

class Db:
    def __init__(self):
        pass

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

def OTO_import_airports():

    df = pd.read_csv("./icaodata.csv")
    # Remove unnamed and useless column at the end of the import
    # df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Add to the database.  This also creates the table if needed
    engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse2", echo=True, echo_pool=True)
    df.to_sql('airport', con=engine, if_exists='fail', method='multi')
    # with engine.connect() as conn:
    #     # Check if the table is there
    #     try:
    #         df.to_sql('flightlog', con=engine, if_exists='fail', method='multi')
    #
    #     except:
    #         # Table exists
    #         print("ICAO table already exists")

def create_db():

    engine = create_engine("mysql+mysqlconnector://tree:password@localhost/fse2")
    session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
