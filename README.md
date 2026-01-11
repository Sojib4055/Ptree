# Semantic Parser Studio

A lightweight natural-language interface for exploring sales data. Ask questions in plain English, see a dependency parse tree in the terminal, and get answers (including full row listings) in a clean web UI.

## What this does
- Parses natural-language questions with spaCy.
- Extracts metrics and filters (year, month, region, product, channel, customer).
- Runs queries against a local SQLite database.
- Returns totals, counts, top results, or full rows.
- Prints the parse tree to the terminal for transparency.

## Quick start (step by step)

1) Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Install the spaCy model (only once)
```bash
python -m spacy download en_core_web_sm
```

4) Run the web app
```bash
uvicorn web_app:app --reload
```

5) Open the UI
- Visit: http://127.0.0.1:8000
- Ask a question. The parse tree prints in the terminal where FastAPI is running.

## Example questions
- Show revenue in 2024
- Which year has most revenue?
- Give me most selling product name in 2024
- List sales orders in north america
- Show revenue in March 2023
- Show revenue from March to May 2023
- Give me sale list in 2023 and 2024 of iphone
- Which region has most orders in 2024

## How it answers questions
1) Clean text (`utils/text_cleaner.py`)
2) Parse sentence with spaCy (`core/parser.py`)
3) Extract metric + filters (`core/tree_walker.py`)
4) Determine intent (`core/intent.py`)
5) Build a logical plan (`core/planner.py`)
6) Execute against SQLite (`execution/executor.py`)
7) Format answer (`response/formatter.py`)

## Data source (SQLite)
The app uses a local SQLite database built from CSVs in:
- `semantic_parser_large_sales_db/data_store/sales_orders/`

Database file:
- `semantic_parser_large_sales_db/sales_orders.db`

Tables:
- `sales_orders_2021`
- `sales_orders_2022`
- `sales_orders_2023`
- `sales_orders_2024`

View:
- `sales_orders_all` (UNION of all year tables)

The DB is created automatically the first time a query runs. If you do not see `sales_orders.db`, run the app and submit any question once.

## Current query capabilities
- Metrics: revenue, order_id (orders), customer_id, product, region, channel, order_date, year
- Aggregations: total (sum), count, top (max)
- Filters: year, month, month range, last N months, region, product, channel, customer_id
- Multi-year queries (e.g., 2023 and 2024)

## Project structure (key files)
- `web_app.py` - FastAPI server + UI
- `engine.py` - Orchestrates parse -> plan -> execute -> format
- `core/parser.py` - spaCy parser
- `core/tree_walker.py` - rule-based metric + filter extraction
- `core/intent.py` - intent detection (READ, LIST, COUNT, AGG_MAX)
- `execution/data_loader.py` - SQLite setup and reads
- `execution/executor.py` - applies filters and aggregations
- `response/formatter.py` - human-readable responses

## Troubleshooting
- Model not found: run `python -m spacy download en_core_web_sm`
- No `sales_orders.db` file: ask any question once to trigger DB creation
- Unexpected answer: check the parse tree in the terminal to see how the sentence was interpreted

## Extending the system
- Add new filters or fields in `core/tree_walker.py`
- Add new aggregations in `execution/executor.py`
- Customize phrasing in `response/formatter.py`
- Swap in a different database or schema in `execution/data_loader.py`

## Notes
- This is a rule-based parser (not an LLM). It is accurate for the supported patterns and fields.
- For broader natural language coverage, expand the rule set or add a learned intent/slot model.
