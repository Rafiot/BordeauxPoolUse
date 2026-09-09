#!/usr/bin/env python3

from datetime import datetime

from fetcher import BordeauxPoolUse

from git import Repo


def update_repo() -> None:
    repo = Repo('./')
    to_add = ['data']
    repo.index.add(to_add)
    repo.index.commit(f"Add data up to {datetime.now()}")
    origin = repo.remote(name='origin')
    origin.push()


if __name__ == "__main__":
    bpu = BordeauxPoolUse()
    bpu.make_jsons()
    # bpu.make_graphs()
    
    update_repo()
