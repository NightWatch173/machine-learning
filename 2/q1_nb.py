"""IMDB Movie review classification using Naive Bayes."""

# Python's stdlib
import math
import re

from contexttimer import Timer as TimeIt
from collections import Counter, defaultdict

from common import accuracy

alnum = re.compile(r'[^A-Za-z]+')


# Data directory
DATA = "data/imdb/"


def clean_line(l):
    # l = l.strip().lower().replace("<br />", "")
    # return re.sub(alnum, ' ', l).strip()
    return l.strip().lower()


def read_file(fn, clean=lambda l: l.strip()):
    with open(DATA + fn) as f:
        # NOTE: Could remove the list here!
        return list(map(clean, f.readlines()))


def read_data(typ):
    train_x = read_file("imdb_%s_text.txt" % typ, clean_line)
    train_y = read_file("imdb_%s_labels.txt" % typ)
    return train_x, train_y


train_x, train_y = read_data("train")
test_x, test_y = read_data("test")


def classify(review, priors, wrd_cnt, wrd_cnt_tot, len_vocab):
    """Classify a review into a class."""

    # Start with only the priors
    probs = priors.copy()

    # Find the probabilities of this review belonging to each class
    for cls in priors.keys():

        for word in review.split():

            # Count of a word may be zero for two reasons:
            # 1 - Word did not occur in reviews of that class
            # 2 - Word did not occur in the entire vocabulary
            cnt = wrd_cnt[cls].get(word, 0)

            # We handle both the cases similarly
            # by Laplace Smoothing
            p = (cnt + 1) / (wrd_cnt_tot[cls] + len_vocab)

            # We use summation of logs to handle underflow issues
            # with low valued probabilities
            probs[cls] += math.log(p)

    # Return the class with maximum probability
    return max(probs, key=probs.get)


def train():
    """Process the training data and return parameters of the model."""

    # Prior probabilites of the data
    cnts = Counter(train_y)
    total = sum(cnts.values())
    priors = {cls: cnt / total for cls, cnt in cnts.items()}

    # Store counts of each word in documents of each class
    wrd_cnt = defaultdict(Counter)
    for r, c in zip(train_x, train_y):
        wrd_cnt[c].update(r.split())

    # Total words in documents of a class
    wrd_cnt_tot = {cls: sum(ctr.values()) for cls, ctr in wrd_cnt.items()}

    # Build a vocabulary of all words in the dataset
    vocab = set()
    for ctr in wrd_cnt.values():
        vocab |= set(ctr.keys())

    return priors, wrd_cnt, wrd_cnt_tot, len(vocab)


def part_a():
    with TimeIt(prefix="Training Naive Bayes"):
        model = train()

    print("")

    with TimeIt(prefix="Finding Training Accuracy"):
        predicted = [classify(review, *model) for review in train_x]
        train_acc = accuracy(predicted, train_y)

    print("\nTraining Accuracy: %.3f\n" % (train_acc * 100))

    with TimeIt(prefix="Finding Testing Accuracy"):
        predicted = [classify(review, *model) for review in test_x]
        test_acc = accuracy(predicted, test_y)

    print("\nTesting Accuracy: %.3f\n" % (test_acc * 100))


if __name__ == '__main__':

    part_a()

    # TODO: Print random & majority accuracy?
