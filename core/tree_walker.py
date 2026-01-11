METRIC_ALIASES = {
    "order": "order_id",
    "orders": "order_id",
    "sales": "revenue",
    "income": "revenue",
    "revenue": "revenue",
}

VALID_METRICS = {
    "order_id",
    "customer_id",
    "product",
    "region",
    "channel",
    "order_date",
    "year",
    "revenue",
}

METRIC_PHRASES = {
    "order id": "order_id",
    "customer id": "customer_id",
    "order date": "order_date",
}

METRIC_HINTS = {
    "sell": "revenue",
    "sale": "revenue",
    "sales": "revenue",
    "revenue": "revenue",
    "income": "revenue",
}

REGION_VALUES = {"asia", "europe", "north_america", "south_america"}
CHANNEL_VALUES = {"online", "partner", "retail"}
PRODUCT_VALUES = {"iphone", "oneplus", "pixel", "samsung", "xiaomi"}

GROUPABLE_FIELDS = {
    "year": "year",
    "month": "month",
    "region": "region",
    "product": "product",
    "channel": "channel",
    "customer": "customer_id",
    "customer_id": "customer_id",
}

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

PREP_TRIGGERS = {"in", "of", "for", "from", "between", "to", "during"}
AGGREGATE_TOKENS = {"total", "sum", "overall"}
RELATIVE_TOKENS = {"last", "past", "previous", "recent"}
QUANTIFIER_MAP = {"couple": 2, "few": 3}


def _normalize_value(value):
    return value.lower().replace("-", "_").replace(" ", "_")


def _token_phrase(token):
    parts = [child.text for child in token.lefts if child.dep_ in {"compound", "amod"}]
    parts.append(token.text)
    return " ".join(parts)


def _infer_filter_from_value(value):
    normalized = _normalize_value(value)
    if normalized in MONTH_MAP:
        return "month", MONTH_MAP[normalized]
    if normalized.isdigit() and len(normalized) == 4:
        return "year", normalized
    if normalized in REGION_VALUES:
        return "region", normalized
    if normalized in CHANNEL_VALUES:
        return "channel", normalized
    if normalized in PRODUCT_VALUES:
        return "product", normalized
    return None, None


def _infer_metric_from_tokens(doc):
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in METRIC_ALIASES:
            return METRIC_ALIASES[lemma]
        if lemma in METRIC_HINTS:
            return METRIC_HINTS[lemma]
    return None


def _resolve_metric_from_token(metric_token):
    phrase = _token_phrase(metric_token).lower()
    if phrase in METRIC_PHRASES:
        return METRIC_PHRASES[phrase]

    lemma = metric_token.lemma_.lower()
    if lemma in METRIC_ALIASES:
        return METRIC_ALIASES[lemma]
    if lemma in VALID_METRICS:
        return lemma

    return None


def _extract_relative_months(doc):
    for token in doc:
        if token.lemma_.lower() not in {"month", "months"}:
            continue

        count = None
        for child in token.children:
            if child.like_num:
                try:
                    count = int(child.text)
                except ValueError:
                    count = None
            if child.lemma_.lower() in QUANTIFIER_MAP:
                count = QUANTIFIER_MAP[child.lemma_.lower()]

        if count is None:
            count = 1

        context = {t.lemma_.lower() for t in token.lefts}
        context.update(t.lemma_.lower() for t in token.ancestors)
        if context & RELATIVE_TOKENS:
            return count

        for child in token.children:
            if child.lemma_.lower() in QUANTIFIER_MAP:
                return count

    return None


def walk(doc):
    metric = None
    filters = {}
    aggregation = None
    group_by = None
    metric_token = None
    metric_hint = None
    months = []
    year_tokens = []

    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in AGGREGATE_TOKENS:
            aggregation = "sum"
        if lemma in GROUPABLE_FIELDS:
            group_by = GROUPABLE_FIELDS[lemma]
        if lemma in METRIC_HINTS:
            metric_hint = METRIC_HINTS[lemma]
        if token.dep_ == "dobj":
            metric_token = token
        if token.dep_ == "pobj" and token.head.text in PREP_TRIGGERS:
            phrase = _token_phrase(token)
            key, value = _infer_filter_from_value(phrase)
            if key == "month":
                months.append(value)
            elif key:
                filters[key] = value
        if token.like_num and token.text.isdigit() and len(token.text) == 4:
            year_tokens.append(token.text)
        if lemma in MONTH_MAP:
            months.append(MONTH_MAP[lemma])

    if "year" not in filters and year_tokens:
        filters["year"] = year_tokens[-1]

    if months:
        month_min = min(months)
        month_max = max(months)
        if month_min == month_max:
            filters["month"] = month_min
        else:
            filters["month_start"] = month_min
            filters["month_end"] = month_max
    else:
        last_months = _extract_relative_months(doc)
        if last_months:
            filters["last_months"] = last_months

    if metric_token:
        metric = _resolve_metric_from_token(metric_token)
    else:
        metric = _infer_metric_from_tokens(doc)

    if not metric and metric_hint:
        metric = metric_hint

    if metric == "revenue" and not aggregation:
        aggregation = "sum"

    return metric, filters, aggregation, group_by
