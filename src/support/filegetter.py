from io import StringIO

import csv
import requests
from src.support.sqlalch import Airport, Assignment
from pathlib import Path
import config
import src.support.util as util
import os
import errno
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from zipfile import ZipFile

class FileGetter:

    def update_to_assignments(self, airports, db):
        return self.__update_assignments(airports, 'to', db)

    def update_from_assignments(self, airports, db):
        return self.__update_assignments(airports, 'from', db)

    def update_airports(self, db):
        url = f'https://server.fseconomy.net/static/library/datafeed_icaodata.zip'
        self.__get_dataframe(url, 'airport', 24 * 365, db, Airport)

    # Creates a ./csv directory to hold csv files if does not exist
    def __create_csv_dir(self):
        self.assignments = []
        self.__CSV_DIR = '../../csv/'
        try:
            os.makedirs(self.__CSV_DIR)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    # Locally used method to get path to csv files.
    def __path(self, filename):
        return Path(self.__CSV_DIR + filename)

    def __get_dataframe (self, url, filename, refresh_time, db, dbClass):
        if db is None:
            filename = f'{filename}.csv'
            self.__get_file_save_csv(url, filename, refresh_time)
            # Open csv file for assignments and import data
            print(f'Reading from {filename}')
            df = pd.read_csv(self.__path(filename))
        # Add to database
        else:
            df = self.__get_file_add_db(url, f'{filename}', db, dbClass, refresh_time)

        df = util.remove_unnamed_from_df(df)
        return df

    def __update_assignments(self, airports, direction, db):

        assignment_query = ''
        for port in airports:
            assignment_query += ('-' + port.icao)
        # remove the first dash
        assignment_query = assignment_query[1:]

        url = f'https://server.fseconomy.net/data?userkey={config.ACCESSCODE}&format=csv&query=icao&search=jobs{direction}&icaos={assignment_query}'
        return self.__get_dataframe(url, 'assignment', 0, db, Assignment)

    def __get_file_add_db(self, url, str_objects, db, class_type, hours=24, **kwargs):
        need_to_download = True
        session = db.session
        try:
            forced_refresh = kwargs['refresh']
        except:
            forced_refresh = False
        try:
            res = session.query(class_type).first()
            if res:
                print(f'{str_objects} exist in the database')
                # Check if recent
                if datetime.now() < res.timestamp + timedelta(hours=hours) and not forced_refresh:
                    ('Database entries are recent, not updating')
                    need_to_download = False
                else:
                    # Clear assignments
                    session.query(class_type).delete()
                    session.commit()

        except:
            print('No entries in the database.')
            pass

        if need_to_download:
            print(f'Downloading {str_objects}')

            if url[-4:] == '.zip':
                response = requests.get(url, stream=True)
                self.__create_csv_dir()
                with open(f'./csv/{str_objects}.zip', 'wb') as fd:
                    for chunk in response.iter_content(chunk_size=512):
                        fd.write(chunk)

                df = pd.read_csv(f'./csv/{str_objects}.zip')
            else:
                response = requests.get(url)
                df = pd.read_csv(StringIO(response.text))

            df = util.remove_unnamed_from_df(df)
            df = util.change_nan_to_none(df)

            for item in df.iterrows():
                data = item[1].array
                assign = class_type(data=item)
                session.add(assign)

            session.commit()
            session.flush()
            return df


        else:
            print(f'{str_objects} have not been downloaded. '
                  f'{str_objects} is within {hours} hours of being updated.  To force update, use "refresh=True" in method call')
            return pd.read_sql_table(f'{str_objects}', db.engine)


    def __get_file_save_csv(self, url, filename, hours, **kwargs):
        forced_refresh = kwargs.get('refresh', False)
        self.__create_csv_dir()
        file = Path(self.__CSV_DIR + filename)
        need_to_download = True

        if file.exists():
            # update if not updated recently
            last_update = datetime.fromtimestamp(file.stat().st_mtime)
            if datetime.now() < last_update + timedelta(hours=hours) and not forced_refresh:
                need_to_download = False

        if need_to_download:
            print(f'Downloading {filename}')
            response = requests.get(url)
            # Check if it is a zip file
            response = requests.get(url)
            if url[-4:] == '.zip':
                z = ZipFile(BytesIO(response.content))
                z.extractall('airports.')

            else:
                with open(file, 'w', newline='') as savefile:
                    writer = csv.writer(savefile)
                    for line in response.iter_lines():
                        writer.writerow(line.decode('utf-8').split(','))

            print(f'{filename} saved')
        else:
            print(f'Assignment have not been downloaded. '
                  f'{filename} is within {hours} of being updated.')