
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

    fp = flightpath.FlightPath('8ka', 'kpdx', exclude='water')
    fp.add_assignments()
    res = assignment_planner.FromToPlanner(fp, 224, 2, 200)
    # fp.plot(plt, include_airports=True)
    # plt.show()



