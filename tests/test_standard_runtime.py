import shutil
from pathlib import Path

import pytest
from flask import Flask

from app.runtime.standard import run_standard_analysis
from app.runtime.upload_service import UploadService
from app.services.tools import standardized_analysis_tools as tools


SAMPLE_CSV = Path('app/sample_data/sample_data_template.csv')
SAMPLE_SHAPEFILE_ZIP = Path('app/sample_data/sample_boundary_template.zip')


@pytest.fixture
def flask_app(tmp_path):
    """Provide a minimal Flask app context with isolated upload storage."""

    app = Flask(__name__)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)

    with app.app_context():
        yield app


def _prepare_session(upload_service: UploadService, session_id: str) -> Path:
    session_dir = upload_service.session_dir(session_id)
    shutil.copyfile(SAMPLE_CSV, session_dir / "raw_data.csv")
    shutil.copyfile(SAMPLE_SHAPEFILE_ZIP, session_dir / "raw_shapefile.zip")
    return session_dir


def test_standard_runtime_analysis_generates_results(flask_app):
    session_id = "standard-runtime-test"
    upload_service = UploadService()
    session_dir = _prepare_session(upload_service, session_id)

    try:
        result = run_standard_analysis(session_id)

        assert result["status"] == "success"
        assert result["analysis_type"] == "composite_scoring"
        assert result.get("variables_used")

        overview = tools.get_session_status(session_id)
        assert overview["csv_loaded"] is True
        assert overview["shapefile_loaded"] is True

    finally:
        shutil.rmtree(session_dir, ignore_errors=True)
