import numpy as np

# prediction function
def predict(X, w, y=None):
    # X_new: Nsample x (d+1)
    # w: (d+1) x 1
    # y_new: Nsample

    y_hat = np.dot(X, w)
    loss = np.mean((y_hat - y) ** 2)

    return y_hat, loss

# training function
def train(X_train, y_train, X_val, y_val):
    N_train = X_train.shape[0]

    # initialization
    w = np.zeros([X_train.shape[1], 1])
    # w: (d+1)x1

    losses_train = []

    w_best = None
    epoch_best = 0

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
            
        losses_train.append(loss_this_epoch / N_train)

    return epoch_best, w_best, losses_train

   
# settings
alpha = 0.001      # learning rate
batch_size = 20    # batch size
MaxIter = 100        # Maximum iteration