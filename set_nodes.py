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
from sqlalch import Airport, Base
from sys import stdout

MAX_DISTANCE_FOR_CALCS = 500; # nautical miles


class AirportDistance(Base):
    __tablename__ = 'airport_distance'

    from_icao = Column(String(5), primary_key=True)
    to_icao = Column(String(5), primary_key=True)
    distance = Column(Float)
    bearing = Column(Float)

    def __init__ (self, froma, toa, dist, bear):
        self.from_icao = froma
        self.to_icao = toa
        self.distance = dist
        self.bearing = bear


class AirportsWithin5(AirportDistance):
    pass

class AirportsWithin10(AirportDistance):
    pass

class AirportsWithin25(AirportDistance):
    pass

def chunk_and_range(db):
    with db.engine.connect() as conn:

        stmt = select(Airport)
        airports = conn.execute(stmt).fetchall()

    # For each airport, find the distance and bearing to each other airport
    MAX_WORKERS = cpu_count() - 1

    # airports = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    chunk_size = math.ceil(len(airports) / MAX_WORKERS)
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS)
    air_total = len(airports)
    last_percent = -1
    for a in airports:
        futures = []
        for i in range(MAX_WORKERS):
            chunk = airports[(i * chunk_size): ((i + 1) * chunk_size)]
            futures.append(executor.submit(chunked_calc_distance_bearing, a, chunk))

        for chunk in concurrent.futures.as_completed(futures):
            results = chunk.result()
            if len(results) > 0:
                db.session.add_all(results)

        db.session.commit()
        with db.engine.connect() as conn:
            stmt = 'SELECT COUNT(DISTINCT {0}) FROM {1}'.format('from_icao', 'airport_distance')
            current = (conn.execute(stmt).fetchone()[0] * 100) // air_total

            if current != last_percent:
                last_percent = current
                stdout.write('\rCalculating airport distances: {}% complete'.format(last_percent))
                stdout.flush()

def chunked_calc_distance_bearing(port1, chunk):
    values = []
    for port2 in chunk:
        if port1 == port2:
            continue
        distance, bearing = calc_distance_bearing(port1, port2)
        if distance < 5:
            values.append(AirportsWithin5(port1.icao, port2.icao, distance, bearing))
        elif distance < 10:
            values.append(AirportsWithin10(port1.icao, port2.icao, distance, bearing))
        elif distance < 25:
            values.append(AirportsWithin25(port1.icao, port2.icao, distance, bearing))

    return values


def calc_distance_bearing(port1, port2):
    if port1 == port2:
        return 0, 0
    # Calculate distance in nautical miles using great circles, or the Haversine equation.

    R = 3440;
    phi1 = port1.lat * math.pi / 180
    phi2 = port2.lat * math.pi / 180
    deltaphi = (port2.lat - port1.lat) * math.pi / 180
    deltalambda = (port2.lon - port1.lon) * math.pi / 180

    a = math.sin(deltaphi / 2) * math.sin(deltaphi / 2) + math.cos(phi1) * math.cos(phi2) * \
        math.sin(deltalambda / 2) * math.sin(deltalambda / 2)
    d = 2 * R * math.asin(math.sqrt(a))

    # Calculate bearing from _initial_ location, port1
    y = math.sin(deltalambda) * math.cos(phi2);
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(deltalambda);
    theta = math.atan2(y, x);
    brng = (theta * 180 / math.pi + 360) % 360; # in degrees
    return d, brng

def OTO_calculate_airport_distances(db):

    db.base.metadata.create_all(db.engine)
    with db.engine.connect() as conn:
        exist = conn.execute(select(AirportDistance)).fetchone()
        if not exist:
            chunk_and_range(db)



