import numpy as np

from sklearn.model_selection import train_test_split

import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.utils.data import Dataset, DataLoader
from torch.autograd import Variable

from common import load_data, write_csv


trX, trY, tsX = load_data()
classes, trYi = np.unique(trY, return_inverse=True)


class Sketches(Dataset):

    def __init__(self, X, Y=None):
        self.X = X
        self.Y = Y

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx] / 255
        y = -1

        if self.Y is not None:
            y = self.Y[idx]

        return x, y


class ConvNet(nn.Module):
    def __init__(self):
        super(ConvNet, self).__init__()

        channels = 30
        self.conv = nn.Conv2d(1, channels, kernel_size=5)

        # Reduce image size by 1/4th ?
        self.mp = nn.MaxPool2d(kernel_size=4)

        img_size = (28 + 1 - self.conv.kernel_size[0]) // 4
        self.fc = nn.Linear(channels * (img_size ** 2), 20)

    def forward(self, x):
        in_size = x.size(0)
        # print(x.size())
        x = self.conv(x)
        # print(x.size())
        x = self.mp(x)
        # print(x.size())
        x = F.relu(x)
        x = x.view(in_size, -1)
        # print(x.size())
        x = self.fc(x)
        # print(x.size())
        # exit()
        return x


def train(net, train_data, dev_data=None,
          max_epochs=100, learning_rate=0.001, quiet=False):

    # Loss and Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(net.parameters(), lr=learning_rate)

    for epoch in range(max_epochs):
        for i, (images, labels) in enumerate(train_data):

            # Convert torch tensor to Variable
            images = Variable(images.view(-1, 1, 28, 28).float())
            labels = Variable(labels)

            # Zero the gradient buffer
            optimizer.zero_grad()

            # Forward Propagation
            outputs = net(images)

            # Calculate loss at output layer
            loss = criterion(outputs, labels)

            # Backpropagate the loss
            loss.backward()

            # Update weights
            optimizer.step()

        if not quiet:
            print(
                # "\r",
                "Epoch [%3d/%3d]" % (epoch + 1, max_epochs),
                "| Train Loss: %.4f" % loss.data[0],
                "| Train Acc: %.4f" % predict(
                    net, train_data, return_acc=True),
                "| Dev Acc: %.4f" % predict(net, dev_data, return_acc=True),
                # sep=" ",
                # end="",
                flush=True,
            )

        # if not quiet and not (epoch + 1) % 10:
        #     print("\n")

    if not quiet:
        print("\n")


def predict(net, data, return_acc=False):

    if not data:
        return -1

    predictions = []
    correct, total = 0, 0

    for images, labels in data:
        images = Variable(images.view(-1, 1, 28, 28).float())
        outputs = net(images)

        _, batch_predictions = torch.max(outputs.data, 1)

        predictions.extend(list(batch_predictions))

        total += labels.size(0)
        correct += (batch_predictions == labels).sum()

    if return_acc:
        return correct / total
    else:
        return predictions


if __name__ == '__main__':

    # Hyper Parameters
    max_epochs = 100
    learning_rate = 0.01

    batch_size = 250

    # Data
    trX_, tvX_, trY_, tvY_ = train_test_split(trX, trYi, test_size=0.3)
    trD = DataLoader(Sketches(trX_, trY_), batch_size, shuffle=True)
    tvD = DataLoader(Sketches(tvX_, tvY_), batch_size, shuffle=False)

    # Build the network
    net = ConvNet()

    print(
        "max_epochs: ", max_epochs,
        "learning_rate: ", learning_rate,
        "batch_size: ", batch_size
    )
    print(net)

    # Train it
    train(net, trD, tvD, max_epochs, learning_rate)

    # Turn shuffle off when computing predictions
    tsD = DataLoader(Sketches(tsX), batch_size, shuffle=False)
    tsP = classes[predict(net, tsD)]
    write_csv("conv_net.csv", tsP)
