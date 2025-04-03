# Paper to Slides

LLM（大規模言語モデル）を使用して学術論文からプレゼンテーションスライドを自動生成するPythonツールです。

## 特徴

- 学術論文をPDF形式でアップロード
- 論文からテキストと図表を抽出
- LLMを使用して要約とキーポイントを生成
- プレゼンテーションスライドを自動作成
- スライドテンプレートとスタイルのカスタマイズ

## 技術スタック

- バックエンド: FastAPI
- PDF処理: PyPDF2/pdfminer.six
- LLM統合: OpenAI API/Anthropic Claude
- PowerPoint生成: python-pptx
- データストレージ: SQLite/PostgreSQL

## 始め方

### 前提条件

- Python 3.9以上
- Poetry（オプション、依存関係管理用）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/takuyakubo/paper-to-slides.git
cd paper-to-slides

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .envファイルにAPIキーを入力
```

### アプリケーションの実行

```bash
uvicorn app.main:app --reload
```

APIドキュメントは `http://localhost:8000/docs` で確認できます。

## 仕様書

詳細な仕様書とドキュメントは `docs` ディレクトリにあります：

- [技術仕様書](docs/技術仕様書.md) - システムアーキテクチャと技術詳細
- [ユーザーガイド](docs/ユーザーガイド.md) - インストールと使用方法
- [API仕様書](docs/API仕様書.md) - APIエンドポイントの詳細
