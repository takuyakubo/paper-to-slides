# Paper to Slides API仕様書

## 概要

Paper to SlidesのREST APIは、学術論文のPDFファイルをアップロードし、LLM（大規模言語モデル）を活用して論文を解析し、プレゼンテーションスライドを自動生成するための機能を提供します。

このドキュメントでは、Paper to Slides APIの全エンドポイント、リクエスト/レスポンス形式、および主要なデータ構造を説明します。

## ベースURL

```
http://localhost:8000/api
```

## 認証

現在のバージョンでは、認証は実装されていません。将来のバージョンでは、JWT（JSON Web Token）ベースの認証が実装される予定です。

## APIエンドポイント

### 論文管理 API

#### 論文アップロード

論文のPDFファイルをアップロードし、テキストと図表の抽出処理を開始します。

```
POST /papers/upload
```

**リクエスト**:

Content-Type: `multipart/form-data`

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| file       | File   | はい | PDFファイル         |
| title      | String | いいえ | 論文のタイトル（省略可） |

**レスポンス**:

```json
{
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Example Paper Title",
  "upload_status": "success",
  "processing_status": "extracting",
  "created_at": "2025-04-03T12:34:56Z"
}
```

**ステータスコード**:

- `201 Created`: 論文が正常にアップロードされました
- `400 Bad Request`: 無効なリクエスト（例：PDFファイルがない）
- `415 Unsupported Media Type`: サポートされていないファイル形式
- `500 Internal Server Error`: サーバーエラー

#### 論文リスト取得

アップロードされた論文のリストを取得します。

```
GET /papers
```

**クエリパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| page       | Integer | いいえ | ページ番号（デフォルト: 1） |
| limit      | Integer | いいえ | 1ページあたりの結果数（デフォルト: 10） |

**レスポンス**:

```json
{
  "papers": [
    {
      "paper_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Example Paper Title 1",
      "processing_status": "completed",
      "created_at": "2025-04-03T12:34:56Z"
    },
    {
      "paper_id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "Example Paper Title 2",
      "processing_status": "analyzing",
      "created_at": "2025-04-03T12:35:56Z"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 10,
  "total_pages": 1
}
```

**ステータスコード**:

- `200 OK`: 成功
- `500 Internal Server Error`: サーバーエラー

#### 論文詳細取得

特定の論文の詳細情報を取得します。

```
GET /papers/{paper_id}
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| paper_id   | UUID   | はい | 論文のID            |

**レスポンス**:

```json
{
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Example Paper Title",
  "authors": ["Author One", "Author Two"],
  "abstract": "This is the abstract of the paper...",
  "sections": [
    {
      "section_id": "sec-1",
      "title": "Introduction",
      "content": "Introduction content..."
    },
    {
      "section_id": "sec-2",
      "title": "Methods",
      "content": "Methods content..."
    }
  ],
  "figures": [
    {
      "figure_id": "fig-1",
      "caption": "Figure 1: Example diagram",
      "page": 2,
      "file_path": "/storage/figures/550e8400-e29b-41d4-a716-446655440000/fig-1.png"
    }
  ],
  "processing_status": "completed",
  "created_at": "2025-04-03T12:34:56Z",
  "updated_at": "2025-04-03T12:40:00Z"
}
```

**ステータスコード**:

- `200 OK`: 成功
- `404 Not Found`: 指定されたIDの論文が見つかりません
- `500 Internal Server Error`: サーバーエラー

#### 論文削除

論文とそれに関連するすべてのデータを削除します。

```
DELETE /papers/{paper_id}
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| paper_id   | UUID   | はい | 論文のID            |

**レスポンス**:

```json
{
  "message": "Paper successfully deleted",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**ステータスコード**:

- `200 OK`: 成功
- `404 Not Found`: 指定されたIDの論文が見つかりません
- `500 Internal Server Error`: サーバーエラー

### LLM処理 API

#### 論文解析

論文をLLMで解析し、要約やキーポイントを生成します。

```
POST /llm/analyze/{paper_id}
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| paper_id   | UUID   | はい | 論文のID            |

**リクエストボディ**:

```json
{
  "model": "gpt-4",
  "temperature": 0.3,
  "summary_length": "medium",
  "language": "en"
}
```

**リクエストパラメータ**:

| パラメータ        | 型     | 必須 | 説明                |
|-------------------|--------|------|---------------------|
| model             | String | いいえ | 使用するLLMモデル（デフォルト: gpt-4） |
| temperature       | Float  | いいえ | 生成のランダム性（0.0〜1.0、デフォルト: 0.3） |
| summary_length    | String | いいえ | 要約の長さ（short/medium/long、デフォルト: medium） |
| language          | String | いいえ | 出力言語（デフォルト: en） |

**レスポンス**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440010",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Analysis started",
  "estimated_time": 120
}
```

**ステータスコード**:

- `202 Accepted`: 解析タスクが開始されました
- `400 Bad Request`: 無効なリクエスト
- `404 Not Found`: 指定されたIDの論文が見つかりません
- `500 Internal Server Error`: サーバーエラー

#### 解析状態の確認

解析タスクの状態を確認します。

```
GET /llm/status/{task_id}
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| task_id    | UUID   | はい | タスクのID          |

**レスポンス**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440010",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-04-03T12:34:56Z",
  "completed_at": "2025-04-03T12:36:56Z"
}
```

**ステータスコード**:

- `200 OK`: 成功
- `404 Not Found`: 指定されたIDのタスクが見つかりません
- `500 Internal Server Error`: サーバーエラー

#### 解析結果の取得

完了した解析タスクの結果を取得します。

```
GET /llm/results/{paper_id}
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| paper_id   | UUID   | はい | 論文のID            |

**レスポンス**:

```json
{
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "This paper presents a novel approach to...",
  "key_points": [
    "First key finding of the paper",
    "Second important contribution",
    "Third significant result"
  ],
  "slide_structure": [
    {
      "slide_type": "title",
      "title": "Paper Title",
      "content": "Authors and Affiliations"
    },
    {
      "slide_type": "outline",
      "title": "Outline",
      "content": "- Introduction\n- Methods\n- Results\n- Discussion"
    }
  ],
  "model_used": "gpt-4",
  "created_at": "2025-04-03T12:36:56Z"
}
```

**ステータスコード**:

- `200 OK`: 成功
- `404 Not Found`: 指定されたIDの論文が見つからないか、解析が完了していません
- `500 Internal Server Error`: サーバーエラー

### スライド生成 API

#### スライド生成

LLM解析結果を基にスライドを生成します。

```
POST /slides/generate/{paper_id}
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| paper_id   | UUID   | はい | 論文のID            |

**リクエストボディ**:

```json
{
  "template": "academic",
  "style": {
    "primary_color": "#4472C4",
    "secondary_color": "#ED7D31",
    "font_family": "Arial"
  },
  "structure": {
    "include_table_of_contents": true,
    "include_references": true,
    "slides_per_section": "auto"
  },
  "language": "en"
}
```

**リクエストパラメータ**:

| パラメータ   | 型     | 必須 | 説明                |
|--------------|--------|------|---------------------|
| template     | String | いいえ | スライドテンプレート（デフォルト: academic） |
| style        | Object | いいえ | スタイル設定        |
| structure    | Object | いいえ | 構造設定            |
| language     | String | いいえ | 出力言語（デフォルト: en） |

**レスポンス**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440020",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Slide generation started",
  "estimated_time": 60
}
```

**ステータスコード**:

- `202 Accepted`: スライド生成タスクが開始されました
- `400 Bad Request`: 無効なリクエスト
- `404 Not Found`: 指定されたIDの論文が見つからないか、解析が完了していません
- `500 Internal Server Error`: サーバーエラー

#### スライド生成状態の確認

スライド生成タスクの状態を確認します。

```
GET /slides/status/{task_id}
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| task_id    | UUID   | はい | タスクのID          |

**レスポンス**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440020",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "slide_id": "550e8400-e29b-41d4-a716-446655440030",
  "created_at": "2025-04-03T12:38:56Z",
  "completed_at": "2025-04-03T12:39:56Z"
}
```

**ステータスコード**:

- `200 OK`: 成功
- `404 Not Found`: 指定されたIDのタスクが見つかりません
- `500 Internal Server Error`: サーバーエラー

#### スライド情報の取得

生成されたスライドの情報を取得します。

```
GET /slides/{slide_id}
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| slide_id   | UUID   | はい | スライドのID        |

**レスポンス**:

```json
{
  "slide_id": "550e8400-e29b-41d4-a716-446655440030",
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Example Paper Title",
  "template": "academic",
  "slide_count": 15,
  "file_format": "pptx",
  "file_size": 1024000,
  "created_at": "2025-04-03T12:39:56Z",
  "download_url": "/api/slides/550e8400-e29b-41d4-a716-446655440030/download"
}
```

**ステータスコード**:

- `200 OK`: 成功
- `404 Not Found`: 指定されたIDのスライドが見つかりません
- `500 Internal Server Error`: サーバーエラー

#### スライドのダウンロード

生成されたスライドファイルをダウンロードします。

```
GET /slides/{slide_id}/download
```

**パスパラメータ**:

| パラメータ | 型     | 必須 | 説明                |
|------------|--------|------|---------------------|
| slide_id   | UUID   | はい | スライドのID        |

**レスポンス**:

PowerPointファイル（Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation）

**ステータスコード**:

- `200 OK`: 成功
- `404 Not Found`: 指定されたIDのスライドが見つかりません
- `500 Internal Server Error`: サーバーエラー

## エラーレスポンス

すべてのAPIエラーは以下の形式で返されます：

```json
{
  "error": {
    "code": "error_code",
    "message": "詳細なエラーメッセージ",
    "details": {} 
  }
}
```

## 共通のエラーコード

| ステータスコード | エラーコード        | 説明                |
|------------------|---------------------|---------------------|
| 400              | invalid_request     | リクエストが無効です |
| 401              | unauthorized        | 認証が必要です      |
| 403              | forbidden           | アクセス権限がありません |
| 404              | not_found           | リソースが見つかりません |
| 415              | unsupported_media   | サポートされていないメディアタイプ |
| 429              | too_many_requests   | リクエスト回数の制限を超えました |
| 500              | server_error        | サーバー内部エラー  |
| 503              | service_unavailable | サービスが一時的に利用できません |

## データモデル

### Paper

論文データの構造：

```json
{
  "paper_id": "UUID",
  "title": "String",
  "authors": ["String"],
  "abstract": "String",
  "sections": [
    {
      "section_id": "String",
      "title": "String",
      "content": "String"
    }
  ],
  "figures": [
    {
      "figure_id": "String",
      "caption": "String",
      "page": "Integer",
      "file_path": "String"
    }
  ],
  "references": [
    {
      "reference_id": "String",
      "citation": "String"
    }
  ],
  "processing_status": "String", // extracting, extracted, analyzing, analyzed, error
  "created_at": "DateTime",
  "updated_at": "DateTime"
}
```

### LLMAnalysis

LLM解析結果の構造：

```json
{
  "analysis_id": "UUID",
  "paper_id": "UUID",
  "summary": "String",
  "key_points": ["String"],
  "slide_structure": [
    {
      "slide_type": "String",
      "title": "String",
      "content": "String"
    }
  ],
  "model_used": "String",
  "created_at": "DateTime"
}
```

### Slide

生成されたスライドの構造：

```json
{
  "slide_id": "UUID",
  "paper_id": "UUID",
  "title": "String",
  "template": "String",
  "style": {
    "primary_color": "String",
    "secondary_color": "String",
    "font_family": "String"
  },
  "slide_count": "Integer",
  "file_format": "String",
  "file_size": "Integer",
  "file_path": "String",
  "created_at": "DateTime"
}
```

### Task

非同期タスクの構造：

```json
{
  "task_id": "UUID",
  "task_type": "String", // analyze, generate_slides
  "paper_id": "UUID",
  "status": "String", // processing, completed, failed
  "progress": "Integer", // 0-100
  "result_id": "UUID", // analysis_id or slide_id
  "created_at": "DateTime",
  "updated_at": "DateTime",
  "completed_at": "DateTime"
}
```

## 制限事項

- アップロードできるPDFファイルの最大サイズ: 50MB
- 論文の最大ページ数: 100ページ
- 1時間あたりのAPIリクエスト数: 100回（将来的に実装予定）
- 同時実行タスク数: 5（将来的に実装予定）

## バージョン履歴

- **v0.1.0** (2025-04-01): 初期バージョン
