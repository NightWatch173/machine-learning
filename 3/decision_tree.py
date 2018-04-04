from collections import deque

import numpy as np

from common import accuracy


class Node():

    """Node of a tree."""

    def __init__(self, parent, nsamples, attr_idx=None, children={}):

        # These stored at all nodes - leaf / internal
        self.parent = parent

        # No. of samples of different classes coming at this node
        self.nsamples = nsamples

        # Majority class of the data coming in at this node
        # (this is used to make predictions)
        self.cls = nsamples.argmax()

        # While these are only stored on internal (decision nodes)
        self.attr_idx = attr_idx  # Index of the attribute to make decision on
        self.children = children  # A dictionary of attribute values and child nodes

    def __repr__(self):
        if self.children:
            r = (self.cls, self.attr_idx, len(self.children))
            return "<Node: cls=%r, attr=%r, children=%r>" % r
        else:
            return "<Leaf: cls=%r>" % self.cls


def entropy(Y):
    """
    Calculate entropy from class labels.
    """
    probabilities = np.bincount(Y) / len(Y)
    return -1 * sum(p * np.log2(p) for p in probabilities if p)


def partition(Xa):
    """
    Partition a column based on the unique values it takes.

    { value: [indices where that value occurs in the column] }
    """
    return {v: np.where(Xa == v)[0] for v in np.unique(Xa)}


class DecisionTree():

    def __init__(self, data=None):
        if data is None:
            self.root = None
        else:
            self.root = self._build_tree(data)

    @staticmethod
    def _build_tree(data, parent=None):
        """
        Build a decision tree using ID3 / information gain.

        First column (data[:, 0]) is the output class.
        """

        Y = data[:, 0]
        nsamples = np.bincount(Y)

        # if data is "pure" i.e has examples of a single class
        # then return a leaf node predicting that class
        if len(set(Y)) <= 1:
            return Node(parent, nsamples)

        # Find the attribute that maximizes the gain
        gain, attr_idx = DecisionTree._best_attribute(data)

        # Split if gain is positive
        # TODO: Remove this conidition? since this is resulting in pre-pruned trees?
        if gain > 0:

            this_node = Node(parent, nsamples, attr_idx)

            this_node.children = {
                v: DecisionTree._build_tree(data[p], parent=this_node)
                for v, p in partition(data[:, attr_idx]).items()
            }

            return this_node

        # Otherwise create a leaf node that predicts the majority class
        else:
            return Node(parent, nsamples)

    @staticmethod
    def _best_attribute(data):
        """
        Use information gain to decide which attribute to split on.
        """

        # Need to find these parameters
        best_gain = -1
        best_attr = -1

        Y = data[:, 0]
        X = data[:, 1:]

        # Iterate over each attribute
        for i, Xa in enumerate(X.T):

            # Create partitions over this attribute
            entropy_Y_Xa = sum((len(p) / len(Xa)) * entropy(Y[p])
                               for p in partition(Xa).values())

            gain = entropy(Y) - entropy_Y_Xa

            # TODO: In case of a tie, choose the attribute which appears first in the
            # ordering as given in the training data.
            if gain > best_gain:
                best_gain = gain

                # NOTE: +1 because the data contains output variables at 1st column
                # so attributes/features start from 2nd column
                best_attr = i + 1

        return best_gain, best_attr

    @staticmethod
    def _predict(dtree, x):
        """Predict a single example using dtree."""
        if not dtree.children:
            return dtree.cls
        else:
            child = dtree.children.get(x[dtree.attr_idx])

            # If there isn't a correct outgoing edge
            # then just return the majority class
            if not child:
                return dtree.cls
            else:
                return DecisionTree._predict(child, x)

    def score(self, data):
        """Find accuracy of dtree over data."""
        predictions = [self._predict(self.root, x) for x in data]
        return accuracy(data[:, 0], predictions)

    def height(self):
        return self._height(self.root)

    @staticmethod
    def _height(dtree):
        if not dtree.children:
            return 0
        else:
            return 1 + max(map(DecisionTree._height, dtree.children.values()))

    def node_count(self):
        return self._node_count(self.root)

    @staticmethod
    def _node_count(dtree):
        if not dtree.children:
            return 1
        else:
            return 1 + sum(map(DecisionTree._node_count, dtree.children.values()))

    @staticmethod
    def _remove_node(node):
        parent = node.parent

        # Root can not be removed
        if parent is None:
            return

        # NOTE: Because we are storing children in a dictionary,
        # removal is costlier than it could be
        # TODO: Use lists for children?
        for v, n in parent.children.items():
            if n == node:
                del parent.children[v]
                break

        return parent

    # NOTE: There is a discrepancy in how the tree was built
    # and how it is being iterated upon; fix?
    # TODO: Use DFS instead of BFS?
    def nodes(self):
        """Iterate over all nodes in the tree in BFS order."""

        q = deque([self.root])

        while q:
            node = q.popleft()
            q.extend(node.children.values())

            yield node

    def prune(self):
        """Use reduced error pruning after the tree has been fully built."""

        nodes = list(self.nodes())
        nodes.reverse()

        # Iteate over all nodes and decide whether to keep this or not.
        for node in nodes:

            # No point in checking a leaf node
            if not node.children:
                continue

            # Using majority class, this fraction of data is incorrectly classified
            node_err_rate = min(node.nsamples) / sum(node.nsamples)

            children_err_rate = sum(
                min(child.nsamples) / sum(node.nsamples)
                for child in node.children.values()
            )

            # Creating children is increasing the error
            if children_err_rate > node_err_rate:

                # Remove the subtree rooted at this node
                # and make this node a leaf
                node.children = {}
