import csv
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SALES_DATA_DIR = os.path.join(
    BASE_DIR, "semantic_parser_large_sales_db", "data_store", "sales_orders"
)
ALL_FILE = os.path.join(SALES_DATA_DIR, "all.csv")


def _build_partition_map():
    partition_files = {}
    if not os.path.isdir(SALES_DATA_DIR):
        return partition_files

    for name in os.listdir(SALES_DATA_DIR):
        if name.startswith("year=") and name.endswith(".csv"):
            year = name[len("year=") : -len(".csv")]
            partition_files[year] = os.path.join(SALES_DATA_DIR, name)

    return partition_files


PARTITION_FILES = _build_partition_map()


def _read_csv(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def _select_data_files(filters):
    if filters:
        year = filters.get("year")
        if year in PARTITION_FILES and os.path.exists(PARTITION_FILES[year]):
            return [PARTITION_FILES[year]]

    if os.path.exists(ALL_FILE):
        return [ALL_FILE]

    return [path for path in PARTITION_FILES.values() if os.path.exists(path)]


def load(filters=None):
    rows = []
    for path in _select_data_files(filters):
        rows.extend(_read_csv(path))
    return rows
