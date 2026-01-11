def plan(intent, metric, filters, aggregation=None, group_by=None):
    return {
        "intent": intent,
        "metric": metric,
        "filters": filters,
        "aggregation": aggregation,
        "group_by": group_by,
    }
