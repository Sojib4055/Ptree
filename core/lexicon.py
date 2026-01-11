import json
from spacy.matcher import PhraseMatcher

class Lexicon:
    def __init__(self, nlp, schema_path, synonym_path):
        self.matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        self.load(schema_path, synonym_path, nlp)

    def load(self, schema_path, synonym_path, nlp):
        schema = json.load(open(schema_path))
        synonyms = json.load(open(synonym_path))

        patterns = []
        for table, meta in schema["tables"].items():
            patterns.append(nlp.make_doc(table))
            for col in meta["columns"]:
                patterns.append(nlp.make_doc(col))

        for key, values in synonyms.items():
            for v in values:
                patterns.append(nlp.make_doc(v))

        self.matcher.add("DB_ENTITY", patterns)

    def match(self, doc):
        return self.matcher(doc)