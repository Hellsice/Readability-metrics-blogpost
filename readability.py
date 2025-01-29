#%%
import re
import numpy
from dependencies.word import Word
import spacy
from spacy.cli import download


# download('nl_core_news_sm')
import re
alphabets= "([A-Za-z])"
prefixes = "(Dhr|Mevr|Dr|Prof)[.]"
suffixes = "(B.V|N.V|Jr|Sr|Co)"
starters = "(Hij\s|Zij\s|Het\s|Wij\s|Jullie\s|Zij\s|Hun\s|Onze\s|Maar\s|Echter\s|Dat\s|Dit\s|Waar\s|Omdat\s|Als\s|Wanneer\s)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](nl|be|com|net|org|io|gov|edu|me)"
digits = "([0-9])"
multiple_dots = r'\.{2,}'

def split_into_sentences(text: str, metrix='lix') -> list[str]:
    """
    Split the text into sentences.

    If the text contains substrings "<prd>" or "<stop>", they would lead 
    to incorrect splitting because they are used as markers for splitting.

    :param text: text to be split into sentences
    :type text: str

    :return: list of sentences
    :rtype: list[str]
    """
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    text = re.sub(multiple_dots, lambda match: "<prd>" * len(match.group(0)) + "<stop>", text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    if metrix == 'lix':
        text = text.replace(':',':<stop>')
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]: sentences = sentences[:-1]
    return sentences


def get_words(text):
    words = re.findall(r'\b\w+\b', text)
    return words

def get_syllable_count(sentences):
    total_syllables = 0
    for sentence in sentences:
        input_words = sentence.split()
        for input_word in input_words:
            word = Word(input_word)
            syllables = word.get_split_word()
            total_syllables += len(syllables.split('-'))
    return total_syllables

def lix(text):
    sentences = split_into_sentences(text, 'lix')
    words = get_words(text)

    total_words = len(words)
    total_sentences = len(sentences)
    long_words = sum(1 for word in words if len(word) > 6)

    # Calculate LIX
    lix_score = (total_words / total_sentences) + (100 * long_words / total_words) if total_words > 0 and total_sentences > 0 else 0
    lix_score = max(20, lix_score)
    lix_score = min(60, lix_score)
    scaled = (lix_score-20)/(60-20)*100
    return 100 - scaled


def flesch_douma(text):
    sentences = split_into_sentences(text)
    words = get_words(text)
    syllable_count = get_syllable_count(sentences)
    
    avg_sentence_length = len(words)/len(sentences) if sentences else 0
    avg_syl = syllable_count/len(words) if words else 0

    score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syl)
    score = max(0, score)
    score = min(100, score)
    return score


def lexical_density(text):
    nlp = spacy.load("nl_core_news_sm")
    doc = nlp(text)

    lexical_words = [word for word in doc if word.pos_ in {'NOUN', 'VERB', 'ADJ', 'ADV'}]
    total_words = len(get_words(text))
    if total_words == 0:
        return 0
    density = (len(lexical_words) / total_words) * 100
    return 100 - density
