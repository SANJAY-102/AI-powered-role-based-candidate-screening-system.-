"""
Generate a sample ML knowledge base PDF for testing.
This creates a simple PDF with ML concepts that the FAISS embedder can process.

Usage: python create_sample_kb.py
"""
import os
import sys

# We'll use fitz (PyMuPDF) to create a PDF
try:
    import fitz
except ImportError:
    print("PyMuPDF not installed yet. Run: pip install pymupdf")
    sys.exit(1)

ML_CONTENT = """
CHAPTER 1: SUPERVISED LEARNING FUNDAMENTALS

1.1 Introduction to Machine Learning

Machine learning is a subfield of artificial intelligence that focuses on building systems that learn from data.
Unlike traditional programming where rules are explicitly coded, machine learning algorithms discover patterns
and relationships in data to make predictions or decisions. The field has three main paradigms: supervised learning,
unsupervised learning, and reinforcement learning.

In supervised learning, the algorithm is trained on labeled data — input-output pairs where the correct answer
is known. The goal is to learn a mapping function from inputs to outputs that generalizes well to unseen data.
Common supervised learning tasks include classification (predicting a discrete label) and regression (predicting
a continuous value).

1.2 Linear Regression

Linear regression is one of the simplest and most interpretable machine learning algorithms. It models the
relationship between a dependent variable y and one or more independent variables X using a linear equation:
y = w0 + w1*x1 + w2*x2 + ... + wn*xn. The coefficients (weights) are learned by minimizing the sum of
squared residuals between predicted and actual values, known as Ordinary Least Squares (OLS).

The cost function for linear regression is the Mean Squared Error (MSE): J(w) = (1/n) * sum((yi - y_hat_i)^2).
Gradient descent can be used to minimize this cost function iteratively by updating weights in the direction
of steepest descent: w = w - alpha * dJ/dw, where alpha is the learning rate.

Regularization techniques like Ridge (L2) and Lasso (L1) regression add penalty terms to prevent overfitting.
Ridge adds lambda * sum(w^2) to the cost function, shrinking coefficients toward zero. Lasso adds lambda * sum(|w|),
which can drive some coefficients exactly to zero, performing feature selection.

1.3 Logistic Regression

Despite its name, logistic regression is a classification algorithm. It uses the sigmoid function
sigma(z) = 1 / (1 + exp(-z)) to map linear predictions to probabilities between 0 and 1. The decision
boundary is typically set at 0.5. For multi-class problems, softmax regression generalizes logistic regression
using the softmax function.

The loss function for logistic regression is binary cross-entropy:
L = -[y * log(p) + (1-y) * log(1-p)], where p is the predicted probability. This is derived from maximum
likelihood estimation and is convex, guaranteeing a global minimum.

1.4 Decision Trees

Decision trees partition the feature space into rectangular regions using a series of binary splits.
At each internal node, the algorithm selects the feature and threshold that best separates the data.
Common splitting criteria include Gini impurity (used in CART) and information gain (used in ID3 and C4.5).

Gini impurity measures the probability of misclassification: Gini = 1 - sum(p_i^2), where p_i is the
proportion of class i samples. Information gain uses entropy: H = -sum(p_i * log2(p_i)). A split is
chosen to maximize the reduction in impurity.

Decision trees are prone to overfitting, especially when grown deep. Pruning techniques (pre-pruning
and post-pruning) help control tree complexity. Setting maximum depth, minimum samples per leaf, and
minimum samples for splitting are common pre-pruning strategies.

1.5 Random Forests

Random forests are an ensemble method that combines multiple decision trees to improve prediction accuracy
and reduce overfitting. Each tree is trained on a bootstrap sample (random sample with replacement) of the
training data, and at each split, only a random subset of features is considered. This introduces diversity
among the trees.

The final prediction is made by majority voting (classification) or averaging (regression) across all trees.
The out-of-bag (OOB) error provides an unbiased estimate of the generalization error without needing a
separate validation set. Feature importance can be measured by the average decrease in impurity across all
trees where a feature is used for splitting.

CHAPTER 2: NEURAL NETWORKS AND DEEP LEARNING

2.1 Artificial Neural Networks

An artificial neural network consists of layers of interconnected nodes (neurons). Each neuron computes
a weighted sum of its inputs, adds a bias, and applies an activation function. The most common architecture
is the feedforward neural network, where information flows from input to output through hidden layers.

Common activation functions include:
- ReLU (Rectified Linear Unit): f(x) = max(0, x) — most popular for hidden layers
- Sigmoid: f(x) = 1/(1+exp(-x)) — used for binary output
- Tanh: f(x) = (exp(x)-exp(-x))/(exp(x)+exp(-x)) — zero-centered
- Softmax: for multi-class output probabilities

2.2 Backpropagation

Backpropagation is the fundamental algorithm for training neural networks. It computes gradients of the
loss function with respect to each weight using the chain rule of calculus. The process has two phases:
forward pass (computing predictions) and backward pass (computing gradients).

During the forward pass, activations are computed layer by layer. During the backward pass, the error
signal propagates from the output layer back through the network. The chain rule allows us to decompose
the gradient computation: dL/dw = dL/da * da/dz * dz/dw, where a is the activation, z is the pre-activation,
and w is the weight.

2.3 Optimization Algorithms

Stochastic Gradient Descent (SGD) updates weights using a single training example or mini-batch at each step.
Variants include:
- Momentum: accumulates past gradients to accelerate convergence: v_t = beta*v_{t-1} + alpha*gradient
- Adam (Adaptive Moment Estimation): combines momentum with adaptive learning rates per parameter.
  It maintains running averages of both gradients and squared gradients.
- Learning rate scheduling: reduces learning rate over time (step decay, cosine annealing, warm-up)

2.4 Convolutional Neural Networks (CNNs)

CNNs are designed for processing grid-like data such as images. Key components include:
- Convolutional layers: apply learnable filters to extract local features
- Pooling layers: reduce spatial dimensions (max pooling, average pooling)
- Fully connected layers: combine features for final prediction

The convolution operation slides a small filter across the input, computing dot products at each position.
This creates a feature map that captures local patterns. Multiple filters at each layer capture different
features (edges, textures, shapes at different levels of abstraction).

Key architectures include LeNet (1998), AlexNet (2012), VGGNet (2014), GoogLeNet/Inception (2014),
ResNet (2015) with skip connections, and EfficientNet (2019).

2.5 Recurrent Neural Networks (RNNs)

RNNs are designed for sequential data processing. They maintain a hidden state that captures information
from previous time steps: h_t = f(W_h * h_{t-1} + W_x * x_t + b). This allows them to model temporal
dependencies in sequences like text, speech, and time series.

Long Short-Term Memory (LSTM) networks address the vanishing gradient problem with a gating mechanism:
- Forget gate: decides what to discard from cell state
- Input gate: decides what new information to store
- Output gate: decides what to output based on cell state

Gated Recurrent Units (GRUs) simplify LSTMs with fewer parameters by combining the forget and input gates
into a single update gate.

CHAPTER 3: MODEL EVALUATION AND SELECTION

3.1 Evaluation Metrics

For classification:
- Accuracy: correct predictions / total predictions
- Precision: true positives / (true positives + false positives)
- Recall (Sensitivity): true positives / (true positives + false negatives)
- F1 Score: harmonic mean of precision and recall = 2 * (P * R) / (P + R)
- ROC-AUC: area under the Receiver Operating Characteristic curve
- Confusion matrix: table showing true vs predicted labels

For regression:
- MSE (Mean Squared Error): average of squared differences
- RMSE (Root Mean Squared Error): square root of MSE
- MAE (Mean Absolute Error): average of absolute differences
- R-squared: proportion of variance explained by the model

3.2 Cross-Validation

K-fold cross-validation divides the data into K equal folds. The model is trained K times, each time
using K-1 folds for training and the remaining fold for validation. The final performance estimate is
the average across all K folds. Common values are K=5 and K=10.

Stratified K-fold ensures each fold maintains the same class distribution as the original dataset,
which is especially important for imbalanced datasets.

3.3 Bias-Variance Tradeoff

The expected prediction error can be decomposed into three components:
Error = Bias^2 + Variance + Irreducible Error

- High bias (underfitting): model is too simple to capture the underlying pattern
- High variance (overfitting): model is too complex and fits noise in the training data
- The goal is to find the sweet spot that minimizes total error

Techniques to address the tradeoff:
- Regularization (L1, L2) to reduce variance
- Ensemble methods (bagging reduces variance, boosting reduces bias)
- Early stopping in neural network training
- Dropout: randomly zeroing out neurons during training to prevent co-adaptation

3.4 Hyperparameter Tuning

Methods for finding optimal hyperparameters:
- Grid search: exhaustive search over specified parameter grid
- Random search: randomly sampling from parameter distributions (often more efficient)
- Bayesian optimization: uses probabilistic models to guide the search
- Cross-validation should be used with each hyperparameter configuration to estimate performance

CHAPTER 4: UNSUPERVISED LEARNING

4.1 Clustering

K-Means clustering partitions data into K clusters by minimizing within-cluster sum of squares.
The algorithm alternates between assigning points to nearest centroids and updating centroids to
cluster means. Initialization matters — K-means++ provides better initial centroids.

DBSCAN (Density-Based Spatial Clustering) groups points that are closely packed together, marking
outliers as noise. It requires two parameters: epsilon (neighborhood radius) and min_samples.
Unlike K-means, it can discover clusters of arbitrary shape and doesn't require specifying K.

4.2 Dimensionality Reduction

Principal Component Analysis (PCA) finds the directions of maximum variance in the data and projects
it onto a lower-dimensional subspace. The principal components are the eigenvectors of the covariance
matrix. PCA preserves global structure but may lose important local relationships.

t-SNE (t-distributed Stochastic Neighbor Embedding) is a nonlinear technique primarily used for
visualization. It preserves local neighborhood structure, making it excellent for visualizing
high-dimensional data in 2D or 3D. However, it's computationally expensive and the results
can vary with different hyperparameters (perplexity).

CHAPTER 5: NATURAL LANGUAGE PROCESSING

5.1 Text Representation

Bag of Words (BoW) represents text as a vector of word frequencies, ignoring word order.
TF-IDF (Term Frequency-Inverse Document Frequency) improves on BoW by weighting words based
on their importance: rare words across documents get higher weight.

Word embeddings (Word2Vec, GloVe) represent words as dense vectors in a continuous space where
semantically similar words are close together. Word2Vec uses either Skip-gram (predict context
from word) or CBOW (predict word from context) architectures.

5.2 Transformer Architecture

The Transformer architecture, introduced in "Attention Is All You Need" (2017), revolutionized NLP.
Key innovations include:
- Self-attention mechanism: each token attends to all other tokens, computing attention weights
  based on query-key-value projections
- Multi-head attention: multiple attention heads capture different types of relationships
- Positional encoding: since there's no recurrence, position information is added via sine/cosine functions
- Layer normalization and residual connections for stable training

BERT (Bidirectional Encoder Representations from Transformers) uses masked language modeling for
pre-training, learning bidirectional context. GPT (Generative Pre-trained Transformer) uses
autoregressive language modeling, predicting the next token given previous tokens.
"""

def create_pdf(content: str, output_path: str):
    """Create a PDF file with the given text content using line-by-line insertion."""
    doc = fitz.open()  # New empty PDF

    # Page dimensions
    page_width = 612
    page_height = 792
    margin_left = 72
    margin_top = 72
    margin_bottom = 72
    line_height = 14
    max_y = page_height - margin_bottom
    fontsize = 10
    fontname = "helv"
    max_chars_per_line = 90  # approximate chars that fit in the line width

    lines = content.strip().split('\n')
    page = doc.new_page(width=page_width, height=page_height)
    y = margin_top
    page_num = 1

    for line in lines:
        # Word-wrap long lines
        if len(line) > max_chars_per_line:
            words = line.split()
            wrapped = ""
            for word in words:
                test = wrapped + (" " if wrapped else "") + word
                if len(test) > max_chars_per_line:
                    # Write the current wrapped line
                    if y + line_height > max_y:
                        page = doc.new_page(width=page_width, height=page_height)
                        y = margin_top
                        page_num += 1
                    page.insert_text(
                        fitz.Point(margin_left, y),
                        wrapped,
                        fontsize=fontsize,
                        fontname=fontname,
                    )
                    y += line_height
                    wrapped = word
                else:
                    wrapped = test
            # Write remaining wrapped text
            if wrapped:
                if y + line_height > max_y:
                    page = doc.new_page(width=page_width, height=page_height)
                    y = margin_top
                    page_num += 1
                page.insert_text(
                    fitz.Point(margin_left, y),
                    wrapped,
                    fontsize=fontsize,
                    fontname=fontname,
                )
                y += line_height
        else:
            # Line fits, insert directly
            if y + line_height > max_y:
                page = doc.new_page(width=page_width, height=page_height)
                y = margin_top
                page_num += 1
            if line.strip():  # Only insert non-empty lines
                page.insert_text(
                    fitz.Point(margin_left, y),
                    line,
                    fontsize=fontsize,
                    fontname=fontname,
                )
            y += line_height

    doc.save(output_path)
    doc.close()
    print(f"Created PDF: {output_path} ({page_num} pages)")


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ml_fundamentals.pdf")
    create_pdf(ML_CONTENT, output_path)
    print("Done! You can now run: python rag/embedder.py")

