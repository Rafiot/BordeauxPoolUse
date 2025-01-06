#!/usr/bin/env python3

import json

from collections import defaultdict
from datetime import datetime, date, timedelta
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

    def make_last_weeks_data(self):
        # Max data to load (in days)
        max_days = 30
        today = date.today()
        oldest_day = today - timedelta(days=max_days)
        # get the first monday after that date
        while oldest_day.weekday() != 0:  # 0 for monday
            oldest_day += timedelta(days=1)

        for pool_dir in self.root_storage.iterdir():
            if not pool_dir.is_dir():
                continue
            for zone_dir in pool_dir.iterdir():

                if not zone_dir.is_dir():
                    continue
                all_jsons = sorted([json_file for json_file in zone_dir.rglob('*.json') if date.fromisoformat(json_file.stem) > oldest_day], reverse=True)
                # make weeks lists
                by_week = defaultdict(dict)
                for json_file in all_jsons:
                    week_number = date.fromisoformat(json_file.stem).isocalendar()[1]
                    with json_file.open() as f:
                        for dt, data in json.load(f).items():
                            by_week[week_number].update({dt: data['fmicourante']})

                break
            break
        return by_week

    def make_graphs(self):
        monthly_dirs = {filename.parent for filename in self.root_storage.rglob('*.json')}
        for monthly_dir in monthly_dirs:
            occupancy = []
            record_time = []
            for jsonfile in sorted(list(monthly_dir.iterdir())):
                if jsonfile.suffix != '.json':
                    continue
                with jsonfile.open() as f:
                    day_content = json.load(f)
                for entry in day_content.values():
                    if entry['fmicourante'] > 0:
                        occupancy.append(entry['fmicourante'])
                        record_time.append(datetime.fromisoformat(entry['datemiseajour']).astimezone())
            if occupancy and record_time:
                fig, ax = plt.subplots()
                fig.set_figwidth(50)
                fig.set_figheight(30)
                plt.title(str(monthly_dir))
                plt.plot(record_time, occupancy)
                locator = AutoDateLocator()
                locator.intervald[HOURLY] = [3]
                ax.xaxis.set_major_locator(locator)
                ax.xaxis.set_major_formatter(AutoDateFormatter(locator))
                plt.xticks(rotation=45)
                plt.savefig(monthly_dir / 'graph.png')
                # plt.show()
