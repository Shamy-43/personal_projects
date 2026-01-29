import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
import joblib
import os

# データ読み込み
df = pd.read_csv("data/EURUSD_730days_M5_features.csv", index_col='time', parse_dates=True)

# 特徴量とターゲット
features = [col for col in df.columns if col not in ['target', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']]
X = df[features].values
y = df['target'].values

# データ分割（直近10%を検証用）
split_point = int(len(X) * 0.9)
X_train, X_test = X[:split_point], X[split_point:]
y_train, y_test = y[:split_point], y[split_point:]

models = {
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
    "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
}

results = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    results[name] = acc
    joblib.dump(model, f"models/{name}.pkl")
    print(f"{name}: {acc:.4f}")

# 結果保存
pd.Series(results).to_csv("models/model_performance.csv")
print("\n✅ モデル学習完了。最高性能モデル：", max(results, key=results.get))
