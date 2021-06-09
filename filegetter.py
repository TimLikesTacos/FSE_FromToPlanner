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

    def __init__(self):
        self.assignments = []
        self.__CSV_DIR = './csv/'
        try:
            os.makedirs(self.__CSV_DIR)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def __path(self, filename):
        return Path(self.__CSV_DIR + filename)

    def get_assignments(self, airports):
        filename = 'assignments.csv'
        assignment_query = ''
        for port in airports:
            assignment_query += ('-' + port.icao)
        # remove the first dash
        assignment_query = assignment_query[1:]
        url = f'https://server.fseconomy.net/data?userkey={config.ACCESSCODE}&format=csv&query=icao&search=jobsto&icaos={assignment_query}'

        self.__get_file_and_save(url, filename, 12)
        print(f'Reading from {filename}')
        df = pd.read_csv(self.__path(filename))
        for item in df.iterrows():
            assign = Assignment(data=item)
            self.assignments.append(assign)

        print(f'Reading from {filename} complete.  Added {len(self.assignments)} assignments')
        print(self.assignments[0].__dict__)

    def __get_file_and_save(self, url, filename, hours=24, **kwargs):
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
                  f'{filename} is within {hours} of being updated.  To force update, use "refresh=True" in method call')