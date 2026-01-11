import csv
import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DB_PATH = os.path.join(BASE_DIR, "semantic_parser_large_sales_db", "sales_orders.db")
DATA_DIR = os.path.join(
    BASE_DIR, "semantic_parser_large_sales_db", "data_store", "sales_orders"
)

YEAR_TABLES = {
    "2021": "sales_orders_2021",
    "2022": "sales_orders_2022",
    "2023": "sales_orders_2023",
    "2024": "sales_orders_2024",
}

CSV_YEAR_FILES = {
    "2021": os.path.join(DATA_DIR, "year=2021.csv"),
    "2022": os.path.join(DATA_DIR, "year=2022.csv"),
    "2023": os.path.join(DATA_DIR, "year=2023.csv"),
    "2024": os.path.join(DATA_DIR, "year=2024.csv"),
}

ALL_VIEW = "sales_orders_all"
COLUMNS = [
    "order_id",
    "customer_id",
    "product",
    "region",
    "channel",
    "order_date",
    "year",
    "revenue",
]


def _read_csv_rows(path):
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader]


def _table_exists(cursor, name):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (name,),
    )
    return cursor.fetchone() is not None


def _create_table(cursor, name):
    column_sql = ", ".join(f"{col} TEXT" for col in COLUMNS)
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} ({column_sql})")


def _insert_rows(cursor, table_name, rows):
    if not rows:
        return
    placeholders = ", ".join("?" for _ in COLUMNS)
    values = [[row.get(col, "") for col in COLUMNS] for row in rows]
    cursor.executemany(
        f"INSERT INTO {table_name} ({', '.join(COLUMNS)}) VALUES ({placeholders})",
        values,
    )


def _ensure_year_table(cursor, year, table_name):
    _create_table(cursor, table_name)
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    if count:
        return

    csv_path = CSV_YEAR_FILES.get(year)
    if csv_path and os.path.exists(csv_path):
        rows = _read_csv_rows(csv_path)
    else:
        all_csv = os.path.join(DATA_DIR, "all.csv")
        if not os.path.exists(all_csv):
            raise FileNotFoundError(f"CSV source not found at {all_csv}")
        rows = [row for row in _read_csv_rows(all_csv) if row.get("year") == year]

    _insert_rows(cursor, table_name, rows)


def _ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.cursor()
        for year, table_name in YEAR_TABLES.items():
            _ensure_year_table(cursor, year, table_name)

        cursor.execute(f"DROP VIEW IF EXISTS {ALL_VIEW}")
        union_sql = " UNION ALL ".join(
            f"SELECT * FROM {table_name}" for table_name in YEAR_TABLES.values()
        )
        cursor.execute(f"CREATE VIEW {ALL_VIEW} AS {union_sql}")
        connection.commit()
    finally:
        connection.close()


def _select_table(filters):
    if not filters:
        return ALL_VIEW
    year = filters.get("year")
    if isinstance(year, (list, tuple)):
        return ALL_VIEW
    if year and year in YEAR_TABLES:
        return YEAR_TABLES[year]
    return ALL_VIEW


def load(filters=None):
    _ensure_db()
    table = _select_table(filters or {})
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()
