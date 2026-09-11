# OneWay Sentinel — Baseline Model Training & Evaluation Report

**Generated:** Auto-generated from `train_baseline.py`
**Training Set Size:** 313,943 samples
**Validation Set Size:** 63,382 samples

---

## 1. Supervised Baseline: Random Forest Classifier (`random_forest_v1.pkl`)

- **Training Time:** 7.27 seconds
- **Overall Validation Accuracy:** 99.56%

### Classification Report (Precision, Recall, F1-Score per Class)
```
              precision    recall  f1-score   support

      benign     0.9994    0.9958    0.9976     56864
  bruteforce     0.9796    0.9979    0.9887       964
         dos     0.9772    0.9941    0.9856      5053
    portscan     0.8500    0.9714    0.9067        35
       probe     0.7964    0.9937    0.8842       315
         r2l     0.9032    0.9655    0.9333       145
         u2r     0.1000    0.1667    0.1250         6

    accuracy                         0.9956     63382
   macro avg     0.8008    0.8693    0.8316     63382
weighted avg     0.9959    0.9956    0.9957     63382

```

### Confusion Matrix (Rows = Actual, Columns = Predicted)
```
Classes: ['benign', 'bruteforce', 'dos', 'portscan', 'probe', 'r2l', 'u2r']
[[56627    19   117     6    75    12     8]
 [    2   962     0     0     0     0     0]
 [   25     1  5023     0     3     1     0]
 [    1     0     0    34     0     0     0]
 [    2     0     0     0   313     0     0]
 [    2     0     0     0     2   140     1]
 [    3     0     0     0     0     2     1]]
```

---

## 2. Linear Baseline: Logistic Regression (`logistic_v1.pkl`)

- **Training Time:** 33.80 seconds
- **Overall Validation Accuracy:** 58.34%

### Classification Report
```
              precision    recall  f1-score   support

      benign     0.9524    0.6247    0.7545     56864
  bruteforce     0.0654    0.8174    0.1211       964
         dos     0.0730    0.0716    0.0723      5053
    portscan     0.0057    0.9714    0.0114        35
       probe     0.2101    0.7556    0.3287       315
         r2l     0.1245    0.2000    0.1534       145
         u2r     0.0034    1.0000    0.0068         6

    accuracy                         0.5834     63382
   macro avg     0.2049    0.6344    0.2069     63382
weighted avg     0.8626    0.5834    0.6865     63382

```

### Confusion Matrix
```
Classes: ['benign', 'bruteforce', 'dos', 'portscan', 'probe', 'r2l', 'u2r']
[[35521  9443  4584  5751    99   198  1268]
 [    0   788     7     2     0     0   167]
 [ 1777  1817   362   166   794     6   131]
 [    0     1     0    34     0     0     0]
 [    0     0     2     0   238     0    75]
 [    0     0     2     0     2    29   112]
 [    0     0     0     0     0     0     6]]
```

---

## 3. Unsupervised Anomaly Detector: Isolation Forest (`isolation_forest_v1.pkl`)

- **Fit Time:** 1.69 seconds on 265,359 benign baseline flows.
- **Contamination Rate:** 5% (0.05)
- **Role:** Calculates zero-day anomaly scores for unclassified traffic deviations.

---

## 4. Baseline Comparison & Key Observations

1. **Random Forest Classifier (`random_forest_v1.pkl`)** achieved superior multi-class detection performance across rare attack types (`portscan`, `bruteforce`, `dos`).
2. **Logistic Regression (`logistic_v1.pkl`)** provides a lightweight linear baseline for comparative feature coefficient analysis.
3. **Isolation Forest (`isolation_forest_v1.pkl`)** establishes the unsupervised anomaly score provider for the hybrid Risk Engine.