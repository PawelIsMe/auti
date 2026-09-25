import os


SNAPSHOT_PATH = "data/static_snapshot.jpg"


def get_latest_snapshot():
    if not os.path.exists(SNAPSHOT_PATH):
        return None
    return SNAPSHOT_PATH