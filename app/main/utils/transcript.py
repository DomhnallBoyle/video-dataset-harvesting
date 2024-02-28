import string

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
stemmer = nltk.stem.porter.PorterStemmer()


def stem_tokens(tokens):
    return [stemmer.stem(item) for item in tokens]


def normalize(text):
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))


def is_similar(s1, s2, threshold=0.1, debug=False):
    # https://stackoverflow.com/questions/8897593/how-to-compute-the-similarity-between-two-text-documents

    vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words='english')

    try:
        tfidf = vectorizer.fit_transform([s1, s2])
    except ValueError:
        return False
    similarity = (tfidf * tfidf.T).A[0,1]

    if debug:
        print(similarity)

    return similarity > threshold
