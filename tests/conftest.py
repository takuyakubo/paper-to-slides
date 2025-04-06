import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """
    テスト用のFastAPI TestClientを提供します。
    """
    return TestClient(app)

@pytest.fixture
def test_pdf_path():
    """
    テスト用のPDFファイルパスを提供します。
    """
    # プロジェクトルートからの相対パス
    return os.path.join(os.path.dirname(__file__), "fixtures", "test_paper.pdf")

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    テスト環境をセットアップします。
    テスト開始時に一度だけ実行されます。
    """
    # テスト用の環境変数を設定
    os.environ["ENVIRONMENT"] = "test"
    os.environ["OPENAI_API_KEY"] = "test_openai_key"
    os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
    
    # テスト用のフィクスチャディレクトリを作成
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    if not os.path.exists(fixtures_dir):
        os.makedirs(fixtures_dir)
    
    yield
    
    # テスト終了後のクリーンアップ（必要に応じて）
    pass
