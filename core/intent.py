SUPERLATIVE_TOKENS = {"most", "highest", "max", "maximum", "top"}


def resolve(doc):
    for token in doc:
        if token.lemma_.lower() in SUPERLATIVE_TOKENS:
            return "AGG_MAX"

    for token in doc:
        if token.lemma_.lower() == "list":
            return "LIST"

    root = [t for t in doc if t.head == t][0]
    if root.lemma_ == "list":
        return "LIST"
    if root.lemma_ in ["show", "give"]:
        return "READ"
    if root.lemma_ == "count":
        return "COUNT"
    return "READ"
