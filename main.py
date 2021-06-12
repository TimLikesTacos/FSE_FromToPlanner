
import mysql.connector as mysql
from mysql.connector import errorcode
import requests

import re
import pandas as pd
from io import StringIO
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt

import sqlalch
import set_nodes
import config
from sqlalch import create_db
import flightpath
from filegetter import FileGetter
import assignment_planner


def main():

    # database = Db()
    # print("DB: ", database)
    # sqlalch.create_db()
    # sqlalch.update_pilot_summary(ACCESSCODE, ACCESSCODE)
    #sqlalch.get_flight_log_info(ACCESSCODE, ACCESSCODE, 0)
    #sqlalch.OTO_import_airports()
    db = sqlalch.Db()
    nodes = set_nodes.OTO_calculate_airport_distances(db)





if __name__ == '__main__':
    db = sqlalch.Db()
    airports = db.session.query(sqlalch.Airport).filter(sqlalch.Airport.type != 'water')
    _kpdx = db.session.query(sqlalch.Airport).get('kpdx')
    _8ka = db.session.query(sqlalch.Airport).get('8ka')

    fp = flightpath.FlightPath(_8ka, _kpdx)


    airports_in_path = fp.airports_in(airports)

    for port in sorted(airports_in_path, key=airports_in_path.get):
        dist = airports_in_path[port]
        plt.plot(port.lon, port.lat, marker='o')

    fg = FileGetter()
    # Using csv
    #assignments = fg.get_assignments(airports_in_path)
    # Using the database
    assignments = fg.get_to_assignments(airports_in_path, db)
    # lp = FromToPlanner(fp, assignments)
    # x, y = fp.poly.exterior.xy
    # cx, cy = fp.path.xy
    # plt.plot(y, x)
    # plt.plot(cy, cx)
    #
    # if fp.start_icao:
    #     plt.plot(fp.start_lon, fp.start_lat, marker='o', label='some')
    #     plt.text(fp.start_lon, fp.start_lat, fp.start_icao)
    #
    # if fp.end_icao:
    #     plt.plot(fp.end_lon, fp.end_lat, marker='o', label='some')
    #     plt.text(fp.end_lon, fp.end_lat, fp.end_icao)
    #
    # print(len(sorted_airports))
    # plt.show()



