import spacy
nlp = spacy.load("en_core_web_sm")

def parse(text):
    return nlp(text)