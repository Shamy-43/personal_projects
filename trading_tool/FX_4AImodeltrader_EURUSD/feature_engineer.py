import pandas as pd
import numpy as np

def add_technical_indicators(df):
    df = df.copy()
    
    # 基本指標
    df['ma_5'] = df['close'].rolling(5).mean()
    df['ma_20'] = df['close'].rolling(20).mean()
    df['ma_100'] = df['close'].rolling(100).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    
    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    
    # ATR（ボラティリティ）
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    tr = ranges.max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    
    # ボリューム変化（MT5ではvolumeが存在しない場合、価格変動で代替）
    df['price_change_pct'] = df['close'].pct_change()
    
    # ターゲット：次足の価格変動方向（1=上昇, 0=下落）
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    # 欠損値除去
    df.dropna(inplace=True)
    
    return df

# 使用例：
if __name__ == "__main__":
    df = pd.read_csv("data/EURUSD_730days_M5.csv", index_col='time', parse_dates=True)
    df_clean = add_technical_indicators(df)
    df_clean.to_csv("data/EURUSD_730days_M5_features.csv")
    print(f"✅ 指標追加済み：{len(df_clean)} レコード保存しました。")
