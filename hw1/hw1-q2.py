import argparse

import numpy as np
import matplotlib.pyplot as plt

import utils


def distance(analytic_solution, model_params):
    return np.linalg.norm(analytic_solution - model_params)


def solve_analytically(X, y):
    """
    X (n_points x n_features)
    y (vector of size n_points)

    Q2.1: given X and y, compute the exact, analytic linear regression solution.
    This function should return a vector of size n_features (the same size as
    the weight vector in the LinearRegression class).
    """
    
    # X has bias term in the last column
    
    # Compute the weights (last weight corresponds to bias term):
    # Using pseudo inverse because np.linalg.inv did not work because matrix was singular
    W = np.linalg.pinv(X.transpose().dot(X)).dot(X.transpose()).dot(y) # (n_features,)
        
    return W


class _RegressionModel:
    """
    Base class that allows evaluation code to be shared between the
    LinearRegression and NeuralRegression classes. You should not need to alter
    this class!
    """
    def train_epoch(self, X, y, **kwargs):
        """
        Iterate over (x, y) pairs, compute the weight update for each of them.
        Keyword arguments are passed to update_weight
        """
        for x_i, y_i in zip(X, y):
            self.update_weight(x_i, y_i, **kwargs)

    def evaluate(self, X, y):
        """
        return the mean squared error between the model's predictions for X
        and he ground truth y values
        """
        yhat = self.predict(X)
        error = yhat - y
        squared_error = np.dot(error, error)
        mean_squared_error = squared_error / y.shape[0]
        return np.sqrt(mean_squared_error)


class LinearRegression(_RegressionModel):
    def __init__(self, n_features, **kwargs):
        self.w = np.zeros((n_features))

    def update_weight(self, x_i, y_i, learning_rate=0.001):
        """
        Q2.2a

        x_i, y_i: a single training example

        This function makes an update to the model weights (in other words,
        self.w).
        """
        # gradient of mean squared error loss dL/dy_hat = 2*(y_hat-y)
        grad_loss = 2*(self.predict(x_i) - y_i) # number

        # gradient of y_hat with respect to the parametes d(y_hat)/dw = x_i
        self.w = self.w - learning_rate * (np.dot(grad_loss, x_i))

        return self.w # (n_features,)

    def predict(self, X):
        return np.dot(X, self.w)


class NeuralRegression(_RegressionModel):
    """
    Q2.2b
    """
    def __init__(self, n_features, hidden):
        """
        In this __init__, you should define the weights of the neural
        regression model (for example, there will probably be one weight
        matrix per layer of the model).
        """
        
        # initialize weight matrices with mu = 0.1 and std = 0.1
        self.weights = [np.random.normal(0.1, 0.1, size = (n_features, hidden)),
                        np.random.normal(0.1, 0.1, size = (hidden, 1))]

        # initialize bias vectors
        self.biases = [np.zeros(hidden),
                       np.zeros(1)]

    def update_weight(self, x_i, y_i, learning_rate=0.001):
        """
        x_i, y_i: a single training example

        This function makes an update to the model weights
        """

        # forward pass
        num_layers = len(self.weights)
        hiddens = []
        for i in range(num_layers):
            h = x_i if i == 0 else hiddens[i-1]
            z = np.dot(h, self.weights[i]) + self.biases[i]
            if i < num_layers-1:
                hiddens.append(np.maximum(z,0))
        yhat = z
        
        # backward pass
        grad_z = 2*(yhat - y_i) # gradient dL/dz
        grad_weights = []
        grad_biases = []
        
        for i in range(num_layers - 1, -1, -1):
        
            h = x_i if i == 0 else hiddens[i-1]
            # compute gradient of parameters:
            grad_weights.append(np.dot(h[:,None], grad_z[:,None].T)) # dL/dw
            grad_biases.append(grad_z) # dL/db
        
            # compute gradient of hidden layer after activation function:
            grad_h = np.dot(grad_z, self.weights[i].T) # dL/dh
        
            # compute gradient of hidden layer before activation:
            # (h > 0) to get the gradient of the ReLU
            grad_z = grad_h * (h > 0) # dL/dz
        
        grad_weights.reverse()
        grad_biases.reverse()
        
        # updating the weights
        for i in range(num_layers):
            self.weights[i] -= learning_rate * grad_weights[i]
            self.biases[i] -= learning_rate * grad_biases[i]
            
        return self.weights, self.biases

    def predict(self, X):
        """
        X: a (n_points x n_feats) matrix.

        This function runs the forward pass of the model, returning yhat, a
        vector of size n_points that contains the predicted values for X.

        This function will be called by evaluate(), which is called at the end
        of each epoch in the training loop. It should not be used by
        update_weight because it returns only the final output of the network,
        not any of the intermediate values needed to do backpropagation.
        """
        
         # forward pass
        num_layers = len(self.weights)
        hiddens = []

        for i in range(num_layers):
            h = X if i == 0 else hiddens[i-1]
            z = np.dot(h, self.weights[i]) + self.biases[i]
            if i < num_layers-1:
                hiddens.append(np.maximum(z,0)) # ReLU

        # z (n_points, 1) so we remove last dimension to work with evaluate
        yhat = z.reshape(-1,)
        return yhat


def plot(epochs, train_loss, test_loss):
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.xticks(np.arange(0, epochs[-1] + 1, step=10))
    plt.plot(epochs, train_loss, label='train')
    plt.plot(epochs, test_loss, label='test')
    plt.legend()
    plt.show()


def plot_dist_from_analytic(epochs, dist):
    plt.xlabel('Epoch')
    plt.ylabel('Dist')
    plt.xticks(np.arange(0, epochs[-1] + 1, step=10))
    plt.plot(epochs, dist, label='dist')
    plt.legend()
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model', choices=['linear_regression', 'nn'],
                        help="Which model should the script run?")
    parser.add_argument('-epochs', default=150, type=int,
                        help="""Number of epochs to train for. You should not
                        need to change this value for your plots.""")
    parser.add_argument('-hidden_size', type=int, default=150)
    parser.add_argument('-learning_rate', type=float, default=0.001)
    opt = parser.parse_args()

    utils.configure_seed(seed=42)

    add_bias = opt.model != 'nn'
    data = utils.load_regression_data(bias=add_bias)
    train_X, train_y = data["train"]
    test_X, test_y = data["test"]

    n_points, n_feats = train_X.shape

    # Linear regression has an exact, analytic solution. Implement it in
    # the solve_analytically function defined above.
    if opt.model == "linear_regression":
        analytic_solution = solve_analytically(train_X, train_y)
    else:
        analytic_solution = None

    # initialize the model
    if opt.model == "linear_regression":
        model = LinearRegression(n_feats)
    else:
        model = NeuralRegression(n_feats, opt.hidden_size)

    # training loop
    epochs = np.arange(1, opt.epochs + 1)
    train_losses = []
    test_losses = []
    dist_opt = []
    for epoch in epochs:
        print('Epoch %i... ' % epoch)
        train_order = np.random.permutation(train_X.shape[0])
        train_X = train_X[train_order]
        train_y = train_y[train_order]
        model.train_epoch(train_X, train_y, learning_rate=opt.learning_rate)

        # Evaluate on the train and test data.
        train_losses.append(model.evaluate(train_X, train_y))
        test_losses.append(model.evaluate(test_X, test_y))

        if analytic_solution is not None:
            model_params = model.w
            dist_opt.append(distance(analytic_solution, model_params))

        print('Loss (train): %.3f | Loss (test): %.3f' % (train_losses[-1], test_losses[-1]))

    plot(epochs, train_losses, test_losses)
    if analytic_solution is not None:
        plot_dist_from_analytic(epochs, dist_opt)


if __name__ == '__main__':
    main()