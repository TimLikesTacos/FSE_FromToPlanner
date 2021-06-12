from io import StringIO

import csv
import requests
from sqlalch import Airport, Assignment
from pathlib import Path
import config
import util
import os
import errno
from datetime import datetime, timedelta
import pandas as pd

class FileGetter:

    # Creates a ./csv directory to hold csv files if does not exist
    def __init__(self):
        self.assignments = []
        self.__CSV_DIR = './csv/'
        try:
            os.makedirs(self.__CSV_DIR)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def get_to_assignments(self, airports, db=None):
        return self.__get_assignments(airports, 'to', db)

    def get_from_assignments(self, airports, db=None):
        return self.__get_assignments(airports, 'from', db)

    # Locally used method to get path to csv files.
    def __path(self, filename):
        return Path(self.__CSV_DIR + filename)


    '''Gets assignments from FSEconomy based off of list of airports as parameter
    Parameters:
        airports: List of sqlalch.Airport
    Returns:
        dict: {'from': [sqlalch.Assignment], 'to': [sqlalch.Assignment]
    '''

    def __get_assignments(self, airports, direction, db):

        assignment_query = ''
        for port in airports:
            assignment_query += ('-' + port.icao)
        # remove the first dash
        assignment_query = assignment_query[1:]

        url = f'https://server.fseconomy.net/data?userkey={config.ACCESSCODE}&format=csv&query=icao&search=jobs{direction}&icaos={assignment_query}'
        # Save as CSV file if database is not being used

        if db is None:
            filename = f'{direction}_assignments.csv'
            self.__get_file_save_csv(url, filename, 12)
            # Open csv file for assignments and import data
            print(f'Reading from {filename}')
            df = pd.read_csv(self.__path(filename))
        # Add to database
        else:
            df = self.__get_file_add_db(url, 'assignments', db, Assignment, 12)

        df = util.remove_unnamed_from_df(df)
        return df


    def __get_file_add_db(self, url, str_objects, db, class_type, hours=24, **kwargs):
        need_to_download = True
        session = db.session
        try:
            forced_refresh = kwargs['refresh']
        except:
            forced_refresh = False
        try:
            res = session.query(Assignment).first()
            if res:
                print('Assignments exist in the database')
                # Check if recent
                if datetime.now() < res.timestamp + timedelta(hours=hours) and not forced_refresh:
                    ('Database entries are recent, not updating')
                    need_to_download = False
                else:
                    # Clear assignments
                    session.query(class_type).delete()

        except:
            print('No entries in the database.')
            pass

        if need_to_download:
            print(f'Downloading {str_objects}')
            response = requests.get(url)
            df = pd.read_csv(StringIO(response.text))
            df = util.remove_unnamed_from_df(df)
            for item in df.iterrows():
                data = item[1].array
                assign = Assignment(data=item)
                session.add(assign)

            session.commit()
            session.close()
            return df


        else:
            print(f'Assignment have not been downloaded. '
                  f'{str_objects} is within {hours} of being updated.  To force update, use "refresh=True" in method call')
            return pd.read_sql_table('assignment', db.engine)

    '''
    Local Method used to obtain a file and save it as a csv
    Parameters:
        url: url to obtain file from
        filename: name of file.  Do not include path as it will automatically be saved in './csv/' directory
        hours: this is used to minimize repetative requests when the data does not change often.  If the saved csv
            file is within this many hours from being modified, then the new file will not be downloaded.
            Default = 24 hrs
        kwargs:
            refresh: If True, will download and save the csv not matter what the 'hours' parameter is set to.
    '''
    def __get_file_save_csv(self, url, filename, hours=24, **kwargs):
        file = Path(self.__CSV_DIR + filename)
        need_to_download = True
        try:
            forced_refresh = kwargs['refresh']
        except:
            forced_refresh = False
        if file.exists():
            # update if not updated recently
            last_update = datetime.fromtimestamp(file.stat().st_mtime)
            if datetime.now() < last_update + timedelta(hours=hours) and not forced_refresh:
                need_to_download = False

        if need_to_download:
            print(f'Downloading {filename}')
            response = requests.get(url)
            with open(file, 'w', newline='') as savefile:
                writer = csv.writer(savefile)

                for line in response.iter_lines():
                    writer.writerow(line.decode('utf-8').split(','))
            print(f'{filename} saved')
        else:
            print(f'Assignment have not been downloaded. '
                  f'{filename} is within {hours} of being updated.')