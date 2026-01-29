# 💰 FX自動売買ツール「USDJPY AI Trader」起動手順

## ✅ 前提条件
- MetaTrader5（MT5）をインストール済み  
- MT5アカウントは**デモ口座**で、**USDJPY**のチャートが開いていること  
- PCは24時間起動可能（自動売買は常時動作）

## 🔧 セットアップ手順
1. フォルダ `FX_AutoTrader_USDJPY` を作成
2. このフォルダ内に、以下のファイルをすべて保存：
   - `main.py`
   - `config.ini`
   - `requirements.txt`
3. コマンドプロンプトで以下を実行：
   ```bash
   cd FX_AutoTrader_USDJPY
   pip install -r requirements.txt
   pip install MetaTrader5


残っている課題　

リスク管理: 現在の実装では、損切りと利確めのレベルは固定されています。より柔軟なリスク管理戦略（例：トレーリングストップなど）を導入することで、システムの耐久性を向上させることができます。

パラメータ最適化: EMAとRSIのパラメータ（期間など）は、現在は固定されています。これらのパラメータに対してグリッドサーチや遺伝的アルゴリズムなどの手法を適用することで、より優れたパフォーマンスを実現できる可能性があります。

多様な市場状況への対応: 現在のシステムは特定の市場条件下で最適化されています。異なる市場状況（例：ボラティリティの高い時期や低い時期）に対して、システムがどのように振る舞うかを検討し、必要に応じて対策を講じることが重要です。

エラー処理とフェイルセーフ: システムは、MT5との接続失敗や注文の不正など、予期せぬエラーに対して適切な対応を実装する必要があります。ロギングと通知機能も充実させることで、運用時のトラブルに迅速に対応できるようになります。


実行順番

cd /d D:\dev\personal_projects\trading_tool\FX_AutoTrader_USDJPY

venv\Scripts\activate

pip install -r requirements.txt



python main.py