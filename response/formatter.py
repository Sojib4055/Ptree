MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def _format_month(value):
    try:
        month = int(value)
    except (TypeError, ValueError):
        return str(value)
    return MONTH_NAMES.get(month, str(value))


def _format_filters(filters):
    if not filters:
        return ""

    year = filters.get("year")
    month = filters.get("month")
    month_start = filters.get("month_start")
    month_end = filters.get("month_end")
    last_months = filters.get("last_months")

    phrases = []
    if last_months:
        if year:
            phrases.append(f"in last {last_months} months of {year}")
        else:
            phrases.append(f"in last {last_months} months")
    elif month:
        month_text = _format_month(month)
        if year:
            phrases.append(f"in {month_text} {year}")
        else:
            phrases.append(f"in {month_text}")
    elif month_start and month_end:
        range_text = f"from {_format_month(month_start)} to {_format_month(month_end)}"
        if year:
            range_text += f" {year}"
        phrases.append(range_text)
    elif year:
        phrases.append(f"in {year}")

    other_keys = ["region", "channel", "product", "customer_id"]
    other_filters = [f"{key}={filters[key]}" for key in other_keys if key in filters]
    if other_filters:
        phrases.append("with " + ", ".join(other_filters))

    return " " + " ".join(phrases)


def format(metric, value, filters):
    filter_text = _format_filters(filters)

    if isinstance(value, list):
        return f"Showing {len(value)} rows{filter_text}."

    if isinstance(value, dict):
        aggregation = value.get("aggregation")
        if aggregation == "sum":
            label = "total revenue" if value.get("metric") == "revenue" else f"total {value.get('metric')}"
            return f"The {label}{filter_text} is {value.get('value')}."
        if aggregation == "max":
            group_by = value.get("group_by") or "group"
            metric_label = value.get("metric") or "value"
            key = value.get("key")
            if group_by == "month":
                key = _format_month(key)
            if value.get("basis") == "count":
                return (
                    f"{group_by.title()} with most orders{filter_text} is {key} "
                    f"({value.get('value')} orders)."
                )
            return (
                f"{group_by.title()} with highest {metric_label}{filter_text} is {key} "
                f"({value.get('value')})."
            )

    if value is None:
        return f"No results{filter_text}."

    if metric:
        label = "orders" if metric == "order_id" else metric
        return f"The {label}{filter_text} is {value}."

    return f"Result{filter_text}: {value}."
