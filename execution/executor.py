from datetime import datetime

from .data_loader import load


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_rows(rows, metric):
    total = 0.0
    for row in rows:
        value = _to_number(row.get(metric))
        if value is not None:
            total += value
    return total


def _parse_order_date(row):
    date_str = row.get("order_date")
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def _apply_month_filter(rows, filters):
    month = filters.get("month")
    month_start = filters.get("month_start")
    month_end = filters.get("month_end")

    if not month and not (month_start and month_end):
        return rows

    filtered = []
    for row in rows:
        date_value = _parse_order_date(row)
        if not date_value:
            continue
        row_month = date_value.month
        if month:
            if row_month != int(month):
                continue
        else:
            if row_month < int(month_start) or row_month > int(month_end):
                continue
        filtered.append(row)
    return filtered


def _apply_relative_month_filter(rows, filters):
    last_months = filters.get("last_months")
    if not last_months:
        return rows

    dated_rows = []
    for row in rows:
        date_value = _parse_order_date(row)
        if date_value:
            dated_rows.append((row, date_value))

    if not dated_rows:
        return rows

    max_date = max(date for _, date in dated_rows)
    max_index = max_date.year * 12 + max_date.month
    threshold = max_index - (int(last_months) - 1)

    filtered = []
    for row, date_value in dated_rows:
        row_index = date_value.year * 12 + date_value.month
        if row_index >= threshold:
            filtered.append(row)
    return filtered


def _apply_filters(rows, filters):
    for key, value in filters.items():
        if key in {"month", "month_start", "month_end", "last_months"}:
            continue
        rows = [row for row in rows if row.get(key) == value]

    rows = _apply_month_filter(rows, filters)
    return _apply_relative_month_filter(rows, filters)


def _metric_is_numeric(rows, metric):
    for row in rows:
        value = _to_number(row.get(metric))
        if value is not None:
            return True
    return False


def _group_aggregate(rows, group_by, metric, aggregation):
    grouped = {}
    for row in rows:
        if group_by == "month":
            date_value = _parse_order_date(row)
            if not date_value:
                continue
            key = date_value.month
        else:
            key = row.get(group_by)
        if key is None:
            continue
        if aggregation == "count":
            grouped[key] = grouped.get(key, 0) + 1
        else:
            value = _to_number(row.get(metric))
            if value is None:
                continue
            grouped[key] = grouped.get(key, 0.0) + value
    return grouped


def execute(plan):
    data = load(plan.get("filters"))
    filters = plan.get("filters") or {}
    rows = _apply_filters(data, filters)

    intent = plan.get("intent")
    metric = plan.get("metric")
    aggregation = plan.get("aggregation")
    group_by = plan.get("group_by")

    if intent == "LIST":
        return rows
    if intent == "COUNT":
        return len(rows)
    if intent == "AGG_MAX":
        if not rows:
            return None
        group_by = group_by or "year"
        metric = metric or "revenue"
        if metric not in rows[0]:
            metric = "revenue"
        if metric != "order_id" and not _metric_is_numeric(rows, metric):
            metric = "revenue"
        if metric == "order_id":
            basis = "count"
        else:
            basis = "sum"
        grouped = _group_aggregate(rows, group_by, metric, basis)
        if not grouped:
            return None
        max_key = max(grouped, key=grouped.get)
        return {
            "aggregation": "max",
            "group_by": group_by,
            "metric": metric,
            "value": grouped[max_key],
            "key": max_key,
            "basis": basis,
        }
    if intent == "READ":
        if not rows:
            return None
        if not metric:
            return None
        if aggregation == "sum":
            total = _sum_rows(rows, metric)
            return {"aggregation": "sum", "metric": metric, "value": total}
        return rows[0].get(metric)

    return None
