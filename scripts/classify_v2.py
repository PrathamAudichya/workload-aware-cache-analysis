#!/usr/bin/env python3
"""Rule-based and decision-tree workload classification from gem5 features."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import confusion_matrix, accuracy_score

IN = Path(sys.argv[1] if len(sys.argv) > 1 else "data/o3_features.csv")
OUT = Path("data/o3_classification.csv")
CLASSES = ["compute", "memory", "branch"]
FEATURES = ["int_frac", "fp_frac", "mem_frac", "branch_frac",
            "branch_mpki", "l1d_mpki", "l2_mpki"]
L2_MPKI_MEM = 5.0      # memory-intensive if L2 MPKI above this
BR_MPKI_BRANCH = 5.0   # branch-intensive if branch MPKI above this

def rule(row):
    """Priority: memory pressure first, then branch behavior, else compute."""
    if row["l2_mpki"] > L2_MPKI_MEM:
        return "memory"
    if row["branch_mpki"] > BR_MPKI_BRANCH:
        return "branch"
    return "compute"

df = pd.read_csv(IN)
df["rule_class"] = df.apply(rule, axis=1)
y = df["intended_class"]

print("== Rule-based (L2 MPKI > %.1f -> memory; branch MPKI > %.1f -> branch) =="
      % (L2_MPKI_MEM, BR_MPKI_BRANCH))
print("accuracy: %.3f" % accuracy_score(y, df["rule_class"]))
print(pd.DataFrame(confusion_matrix(y, df["rule_class"], labels=CLASSES),
                   index=[f"true_{c}" for c in CLASSES],
                   columns=[f"pred_{c}" for c in CLASSES]))

X = df[FEATURES].values
tree = DecisionTreeClassifier(max_depth=3, random_state=0)
loo = cross_val_predict(tree, X, y, cv=LeaveOneOut())
df["tree_loo_class"] = loo
print("\n== Decision tree, leave-one-out CV (depth 3) ==")
print("accuracy: %.3f" % accuracy_score(y, loo))
print(pd.DataFrame(confusion_matrix(y, loo, labels=CLASSES),
                   index=[f"true_{c}" for c in CLASSES],
                   columns=[f"pred_{c}" for c in CLASSES]))

tree.fit(X, y)
print("\nTree fit on all 12 (for interpretation only):")
print(export_text(tree, feature_names=FEATURES))
imp = pd.Series(tree.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("Feature importances:\n" + imp[imp > 0].round(3).to_string())

df[["workload", "intended_class", "rule_class", "tree_loo_class",
    "l2_mpki", "branch_mpki"]].to_csv(OUT, index=False)
print(f"\nWrote {OUT}")
