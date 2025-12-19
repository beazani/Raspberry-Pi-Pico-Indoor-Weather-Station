import math

class ComfortML:
    """Predicts thermal comfort (0 or 1) based on age, sex, and temperature using logistic regression."""
    def __init__(self):
        # Training parameters
        self.weights = [0.060531, 0.02913246, -0.2601366 ]   # age, sex, temperature
        self.bias = 0.5626224060032154

        self.mean = [0.81778274, 0.59784226, 25.36569196]
        self.scale = [0.85941693, 0.49033345, 4.31082637]

    def _normalize(self, x):
        return [(x[i] - self.mean[i]) / self.scale[i] for i in range(3)]

    def _sigmoid(self, z):
        return 1 / (1 + math.exp(-z))

    def predict(self, age, sex, temperature):
        x = self._normalize([age, sex, temperature])

        z = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        prob = self._sigmoid(z)

        label = 1 if prob >= 0.6 else 0
        return label, prob
