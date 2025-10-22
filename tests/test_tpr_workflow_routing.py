import os
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from flask import Flask
from werkzeug.datastructures import FileStorage

from app.runtime.tpr.detector import TPRUploadDetector
from app.runtime.tpr.workflow import (
    get_tpr_status,
    initialize_tpr_session,
    process_tpr_message,
    reset_tpr_handler_cache,
    start_tpr_workflow,
)


@pytest.fixture
def flask_app(tmp_path):
    """Provide a minimal Flask app context with an isolated upload folder."""
    app = Flask(__name__)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)
    with app.app_context():
        yield app


@pytest.fixture
def sample_tpr_dataframe():
    """Construct a small dataframe that mimics NMEP TPR structure."""
    return pd.DataFrame(
        {
            "State": ["Adamawa", "Adamawa", "Kwara"],
            "LGA": ["Yola", "Girei", "Ilorin"],
            "WardName": ["Ward 1", "Ward 2", "Ward 3"],
            "FacilityLevel": ["Primary", "Secondary", "Primary"],
            "Tested by RDT (Fever cases)": [120, 80, 150],
            "Positive for malaria by RDT": [30, 20, 45],
            "Tested by Microscopy (Fever cases)": [60, 40, 70],
            "Positive for malaria by Microscopy": [15, 8, 20],
        }
    )


def _make_filestorage_from_df(df: pd.DataFrame, filename: str) -> FileStorage:
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return FileStorage(stream=buffer, filename=filename)


def test_tpr_upload_detector_identifies_nmep_excel(sample_tpr_dataframe):
    storage = _make_filestorage_from_df(sample_tpr_dataframe, "nmep_tpr.xlsx")
    detector = TPRUploadDetector()
    detection = detector.detect(storage)

    assert detection.upload_type == "tpr_excel"
    assert detection.detection_info["is_tpr"] is True
    assert detection.detection_info["metadata"].get("states_available")


def test_tpr_upload_detector_ignores_non_excel(sample_tpr_dataframe, tmp_path):
    csv_path = tmp_path / "random.csv"
    sample_tpr_dataframe.to_csv(csv_path, index=False)
    with csv_path.open("rb") as fh:
        storage = FileStorage(stream=BytesIO(fh.read()), filename="random.csv")
    detector = TPRUploadDetector()
    detection = detector.detect(storage)

    assert detection.upload_type == "standard"
    assert detection.detection_info["is_tpr"] is False


def test_runtime_workflow_end_to_end(flask_app, sample_tpr_dataframe):
    session_id = "test-session"
    try:
        initialize_tpr_session(session_id, sample_tpr_dataframe)
        start_payload = start_tpr_workflow(session_id)

        assert start_payload["workflow"].startswith("tpr")
        assert start_payload.get("message")

        # Provide a state selection to advance the workflow
        result = process_tpr_message(session_id, "Adamawa")
        assert result["workflow"] == "tpr"
        assert result.get("message")

        status = get_tpr_status(session_id)
        assert status["active"] is True
        assert status["selections"].get("state") in {"Adamawa", "adamawa"}
    finally:
        reset_tpr_handler_cache(session_id)
