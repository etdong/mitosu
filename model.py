import numpy as np
import csv

def get_weights():

    # prediction function
    def predict(X, w, y=None):
        # X_new: Nsample x (d+1)
        # w: (d+1) x 1
        # y_new: Nsample

        y_hat = np.dot(X, w)
        loss = np.mean((y_hat - y) ** 2)
        risk = np.mean(np.abs(y_hat - y))

        return y_hat, loss, risk

    # training function
    def train(X_train, y_train, X_val, y_val):
        N_train = X_train.shape[0]

        # initialization
        w = np.zeros([X_train.shape[1], 1])
        # w: (d+1)x1

        losses_train = []
        risks_val = []

        w_best = None
        epoch_best = 0
        risk_best = 10000

        for epoch in range(MaxIter):

            loss_this_epoch = 0
            for b in range(int(np.ceil(N_train/batch_size))):

                X_batch = X_train[b*batch_size: (b+1)*batch_size]
                y_batch = y_train[b*batch_size: (b+1)*batch_size]

                y_hat_batch, loss_batch, _ = predict(X_batch, w, y_batch)
                loss_this_epoch += loss_batch

                # Mini-batch gradient descent
                gradient = np.dot(X_batch.T, (y_hat_batch - y_batch)) / batch_size
                w -= alpha * gradient
                
            # 1. Compute the training loss by averaging loss_this_epoch
            # 2. Perform validation on the validation set by the risk
            # 3. Keep track of the best validation epoch, risk, and the weights
            losses_train.append(loss_this_epoch / N_train)
            _, _, risk_val = predict(X_val, w, y_val)
            risks_val.append(risk_val)
            if risk_val < risk_best:
                risk_best = risk_val
                w_best = w
                epoch_best = epoch

        return risk_best, epoch_best, w_best, losses_train, risks_val

    # reading beatmap data
    with open("data.csv", "r") as f:
        reader = csv.reader(f)
        data = list(reader)

    # making features and labels
    X = np.array([np.array([float(val) for val in entry[1:-1]]) for entry in data[1:]])
    y = np.array([[float(entry[-1]) for entry in data[1:]]]).T

    # Augment feature
    X_ = np.concatenate((np.ones([X.shape[0], 1]), X), axis=1)
    # X_: Nsample x (d+1)

    # normalize features:
    X = (X - np.mean(X, axis=0)) / np.std(X, axis=0)
    y = (y - np.mean(y)) / np.std(y)

    # Randomly shuffle the data
    np.random.seed(314)
    np.random.shuffle(X_)
    np.random.seed(314)
    np.random.shuffle(y)

    X_train = X_[:450]
    y_train = y[:450]

    X_val = X_[450:600]
    y_val = y[450:600]

    X_test = X_[600:]
    y_test = y[600:]

    # settings
    alpha = 0.001      # learning rate
    batch_size = 20    # batch size
    MaxIter = 100        # Maximum iteration

    risk_best, epoch_best, w_best, losses_train, risks_val = train(X_train, y_train, X_val, y_val)

    # Perform test by the weights yielding the best validation performance
    y_hat = np.dot(X_test, w_best)
    test_risk = np.mean(np.abs(y_hat - y_test))

    print('epoch_best: ', epoch_best)
    print('risk_best: ', risk_best)
    print('test_risk: ', test_risk)
    print('w_best: ', w_best)
    return w_best