from utils.text_cleaner import clean
from core.parser import parse
from core.tree_walker import walk
from core.intent import resolve
from core.planner import plan
from execution.executor import execute
from response.formatter import format


def _print_tree_node(token, indent, is_last):
    branch = "`- " if is_last else "|- "
    print(f"{indent}{branch}{token.text} ({token.dep_})")
    children = list(token.children)
    next_indent = indent + ("   " if is_last else "|  ")
    for index, child in enumerate(children):
        _print_tree_node(child, next_indent, index == len(children) - 1)


def _print_parse_tree(doc):
    roots = [t for t in doc if t.head == t]
    if not roots:
        print("Parse tree: <empty>")
        return
    print("Parse tree:")
    for index, root in enumerate(roots):
        _print_tree_node(root, "", index == len(roots) - 1)


def analyze(question, show_tree=False):
    q = clean(question)
    doc = parse(q)
    if show_tree:
        _print_parse_tree(doc)
    metric, filters, aggregation, group_by = walk(doc)
    intent = resolve(doc)
    logical_plan = plan(intent, metric, filters, aggregation, group_by)
    result = execute(logical_plan)
    return {
        "question": question,
        "metric": metric,
        "filters": filters,
        "intent": intent,
        "aggregation": aggregation,
        "group_by": group_by,
        "result": result,
    }


def ask(question, show_tree=False):
    analysis = analyze(question, show_tree=show_tree)
    return format(analysis["metric"], analysis["result"], analysis["filters"])


if __name__ == "__main__":
    print(ask("Show revenue in 2024", show_tree=True))
