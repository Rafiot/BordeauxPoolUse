#!/usr/bin/env python3

import json

from datetime import datetime
from pathlib import Path

import requests


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
            pool_dir = self.root_storage / fields['etablissement_etalib']
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
            day_content[update_timestamp.isoformat()] = fields
            with day_file.open('w') as _fw:
                json.dump(day_content, _fw)
