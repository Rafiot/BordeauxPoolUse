#!/usr/bin/env python3

import json

from datetime import datetime
from pathlib import Path

import requests

#import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, AutoDateFormatter, HOURLY
#import numpy as np


class BordeauxPoolUse():

    def __init__(self):
        self.url = "https://opendata.bordeaux-metropole.fr/api/records/1.0/search/?dataset=bor_frequentation_piscine_tr"
        self.root_storage = Path('data')

    def fetch(self):
        response = requests.get(self.url)
        response.raise_for_status()
        return response.json()

    def make_jsons(self):
        data = self.fetch()
        for entry in data['records']:
            fields = entry['fields']
            pool_dir = self.root_storage / fields['etablissement_etalib'] / fields['fmizonlib']
            update_timestamp = datetime.fromisoformat(fields['datemiseajour'])
            store_dir = pool_dir / str(update_timestamp.year) / f'{update_timestamp.month:02}'
            store_dir.mkdir(parents=True, exist_ok=True)
            day_file = store_dir / f'{update_timestamp.date().isoformat()}.json'
            if day_file.exists():
                with day_file.open() as _f:
                    day_content = json.load(_f)
            else:
                day_content = {}
            if update_timestamp.isoformat() in day_content:
                continue

            # Dirty check so we only add an entry if the data changed
            if updates := sorted(day_content.keys()):
                last_update = updates[-1]
                last_data = day_content[last_update]
                if ({v for k, v in last_data.items() if k != 'datemiseajour'} == {v for k, v in fields.items() if k != 'datemiseajour'}):
                    continue

            day_content[update_timestamp.isoformat()] = fields
            with day_file.open('w') as _fw:
                json.dump(day_content, _fw, indent=2)

    def make_graphs(self):
        monthly_dirs = {filename.parent for filename in self.root_storage.rglob('*.json')}
        for monthly_dir in monthly_dirs:
            occupancy = []
            record_time = []
            for jsonfile in sorted(list(monthly_dir.iterdir())):
                with jsonfile.open() as f:
                    day_content = json.load(f)
                for entry in day_content.values():
                    if entry['fmicourante'] > 0:
                        occupancy.append(entry['fmicourante'])
                        record_time.append(datetime.fromisoformat(entry['datemiseajour']).astimezone())
            if occupancy and record_time:
                fig, ax = plt.subplots()
                plt.title(str(monthly_dir))
                plt.plot(record_time, occupancy)
                locator = AutoDateLocator()
                locator.intervald[HOURLY] = [3]
                ax.xaxis.set_major_locator(locator)
                ax.xaxis.set_major_formatter(AutoDateFormatter(locator))
                plt.xticks(rotation=45)
                plt.savefig(monthly_dir / 'graph.png')
                # plt.show()
