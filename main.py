import os
import numpy as np
from linear_regression import train
from utils import get_training_data

import ossapi

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
api = ossapi.Ossapi(client_id, client_secret)


if __name__ == "__main__":
    data = get_training_data(api.user("h0mygod"))

    X = data[:, :-1]
    y = data[:, -1]

    print(X.shape, y.shape)

    X = (X - np.mean(X, axis=0)) / np.std(X, axis=0)
    y = (y - np.mean(y)) / np.std(y)
    
    X_ = np.concatenate((np.ones([X.shape[0], 1]), X), axis=1)

    training_cutoff = int(X_.shape[0] * 0.6)
    validation_cutoff = int(X_.shape[0] * 0.8)

    X_train = X_[:training_cutoff]
    y_train = y[:training_cutoff]

    X_val = X_[training_cutoff:validation_cutoff]
    y_val = y[training_cutoff:validation_cutoff]

    X_test = X_[validation_cutoff:]
    y_test = y[validation_cutoff:]

    epoch_best, w_best, losses_train = train(X_train, y_train, X_val, y_val)

    # Perform test by the weights yielding the best validation performance
    y_hat = np.dot(X_test, w_best)
    test_risk = np.mean(np.abs(y_hat - y_test))

    print('epoch_best: ', epoch_best)
    print('test_risk: ', test_risk)
    print('w_best: ', w_best)
    