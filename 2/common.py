import matplotlib.pyplot as plt
import seaborn as sn


def accuracy(actual, predicted):
    """Find accuracy of the model."""

    assert len(actual) == len(predicted)

    correct = sum([a == p for (a, p) in zip(actual, predicted)])
    return correct / len(actual)


def make_confusion(actual, predicted):
    """Create a confusion matrix from two list of labels."""

    assert len(actual) == len(predicted)

    # TODO: Not proud of this code - Make Pythonic!

    # Using a dict ensures that classes can be anything
    cm = {
        c: {cc: 0 for cc in set(actual)}
        for c in set(actual)
    }

    # Update entries with counts
    for a, p in zip(actual, predicted):
        cm[a][p] += 1

    # Now convert into a matrix form
    # TODO: See if seaborn can take dictionaries as input
    cmm = []
    for a in sorted(cm):
        cmm.append([cm[a][p] for p in sorted(cm[a])])

    return cmm


def plot_confusion(actual, predicted, ticks, title):
    """Plot the confusion matrix."""

    cm = make_confusion(actual, predicted)
    acc = " - Accuracy - %.2f\%" % (accuracy(actual, predicted) * 100)

    # Could replace the above line by sklearn.metrics.confusion_matrix
    # cm = confusion_matrix(actual, predicted)

    plt.figure(figsize=(10, 7))
    plt.title(title + acc)
    ax = sn.heatmap(cm, fmt="d", annot=True, cbar=False,
                    cmap=sn.cubehelix_palette(15),
                    xticklabels=ticks, yticklabels=ticks)
    ax.set(xlabel="Predicted", ylabel="Actual")

    plt.savefig(title + ".png")
    plt.close()
