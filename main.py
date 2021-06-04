
import mysql.connector as mysql
from mysql.connector import errorcode
import requests

import re
import pandas as pd
from io import StringIO
from sqlalchemy import create_engine, text

import sqlalch
import set_nodes
from db import Db
from sqlalch import create_db


ACCESSCODE = "1D593BCBB727A29D"

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
    main()
    #db.engine()

