# Decision Trees in Machine Learning

This README answers ten questions about decision trees, including their components, split criteria, pruning, and a scikit-learn example.

## 1. What is a decision tree?

A decision tree is a supervised machine-learning model that makes predictions by applying a sequence of questions to input data. Each answer determines which branch to follow, and the final leaf contains the predicted class or value.

For example, to decide whether to go for an outdoor run, a tree might ask:

1. Is it raining?
2. If not, is the temperature comfortable?
3. If both conditions are suitable, predict **Go for a run**; otherwise, predict **Stay indoors**.

## 2. What are the main components of a decision tree?

- **Root node:** The first question or split; it represents the full dataset.
- **Decision node:** A node that tests a feature and splits the data.
- **Branch:** The outcome of a decision that leads to another node.
- **Leaf node:** A terminal node containing the final prediction.

For example, a weather tree could start with the root node **Outlook**, branch into **Sunny**, **Cloudy**, and **Rainy**, and use further decision nodes such as **Humidity** before reaching a leaf such as **Go running** or **Stay indoors**.

## 3. How do classification trees and regression trees differ?

| Classification tree | Regression tree |
|---|---|
| Predicts a categorical class or label. | Predicts a continuous numerical value. |
| Example: classify whether a patient has a disease based on medical test results. | Example: predict tomorrow's temperature from historical weather data. |

## 4. What is Gini impurity, and how does it help choose a split?

Gini impurity measures how mixed the class labels are in a node. It can be interpreted as the probability of misclassifying a randomly selected example if its label were assigned according to the class distribution in that node.

For a node with class proportions \(p_1, p_2, \ldots, p_k\), Gini impurity is:

**Gini = 1 - Σ pᵢ²**

A value of zero means the node contains examples from only one class. When considering a split, the tree calculates the weighted Gini impurity of the resulting child nodes. It prefers the split that produces the greatest reduction in impurity. This is a greedy choice: the best split is selected at the current node without searching every possible complete tree.

## 5. What are entropy and information gain?

**Entropy** measures the uncertainty or class-label disorder in a node. For class proportions \(p_1, p_2, \ldots, p_k\), it is defined as:

**Entropy = -Σ pᵢ log₂(pᵢ)**

Entropy is zero when all examples in a node belong to one class. It is higher when the classes are more evenly represented.

**Information gain** is the reduction in entropy achieved by a split:

**Information gain = parent entropy - weighted child entropy**

A decision tree using information gain prefers the split that reduces uncertainty the most.

## 6. What is overfitting, and how can it be reduced?

Overfitting occurs when a model learns details and noise in its training data too closely. It may perform very well on training examples but generalize poorly to new, unseen examples.

Three ways to reduce overfitting in decision trees are:

1. **Pre-pruning:** Limit tree growth while it is being built, for example by setting `max_depth` or `min_samples_leaf`.
2. **Post-pruning:** Grow the tree first, then remove branches that contribute little to predictive performance. Cost-complexity pruning is one approach.
3. **Ensembling:** Combine predictions from multiple trees. For example, a random forest averages or votes across trees trained on varied samples and features.

## 7. How do pre-pruning and post-pruning differ?

| Pre-pruning | Post-pruning |
|---|---|
| Stops the tree from growing further when a stopping rule is met. | Builds a larger tree first, then removes branches that add little predictive value. |
| Uses limits such as maximum depth or minimum samples required for a split. | Can use cost-complexity pruning to balance tree size against fit. |
| Is computationally simpler, but stopping too early can miss useful patterns. | Can capture more patterns before pruning, but requires building and evaluating a larger tree. |

## 8. How can scikit-learn train a `DecisionTreeClassifier`?

This example uses scikit-learn's built-in Iris dataset, splits it into training and test sets, trains a classifier, and evaluates its accuracy.

```python
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

iris = load_iris()
X = iris.data
y = iris.target

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

model = DecisionTreeClassifier(max_depth=3, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
```

## 9. What do common decision tree parameters control?

| Parameter | Purpose |
|---|---|
| `max_depth` | Sets the maximum number of levels in the tree. Limiting depth can help prevent overfitting. |
| `criterion` | Selects the measure used to evaluate split quality. For classification, common options include `gini`, `entropy`, and `log_loss`. |
| `min_samples_split` | Sets the minimum number of samples a node must contain before it can be split. |
| `min_samples_leaf` | Sets the minimum number of samples required in each leaf node. |

## 10. What might 98% training accuracy and 65% test accuracy indicate?

This large gap may indicate **overfitting**: the model performs very well on the training data but does not generalize as well to unseen data.

Ways to investigate and improve the model include:

- Check that the training and test sets are representative and that there is no data leakage.
- Use cross-validation to estimate performance more reliably.
- Reduce tree complexity with settings such as `max_depth`, `min_samples_split`, or `min_samples_leaf`.
- Apply cost-complexity pruning.
- Collect more representative training data when possible.
- Compare performance using metrics appropriate to the task, especially if the classes are imbalanced.
