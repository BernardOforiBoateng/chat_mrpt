"""Regression tests that cover visualization wiring and dataset persistence."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from flask import Flask

from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
from app.runtime.tpr.workflow import initialize_tpr_session, reset_tpr_handler_cache


@pytest.fixture
def sample_dataset():
    return pd.DataFrame(
        {
            "State": ["TestState", "TestState"],
            "WardName": ["Ward 1", "Ward 2"],
            "FacilityLevel": ["Primary", "Secondary"],
            "Tested by RDT (Fever cases)": [120, 95],
            "Positive for malaria by RDT": [30, 25],
        }
    )


@pytest.fixture
def flask_app(tmp_path):
    app = Flask(__name__)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)
    with app.app_context():
        yield app


def _session_dir(session_id: str) -> Path:
    return Path("instance/uploads") / session_id


def _cleanup_session(session_id: str) -> None:
    reset_tpr_handler_cache(session_id)
    shutil.rmtree(_session_dir(session_id), ignore_errors=True)
    # Also clear any mirrored upload folder entries
    for base in (Path("instance/uploads"),):
        shutil.rmtree(base / session_id, ignore_errors=True)


def test_calculate_tpr_embeds_visualization(sample_dataset):
    session_id = "test-viz-runtime"
    session_dir = _session_dir(session_id)
    try:
        session_dir.mkdir(parents=True, exist_ok=True)

        state_manager = DataAnalysisStateManager(session_id)
        handler = TPRWorkflowHandler(session_id, state_manager, None)
        handler.uploaded_data = sample_dataset
        handler.tpr_selections = {
            "state": "TestState",
            "facility_level": "primary",
            "age_group": "u5",
        }

        # Pretend the tool already produced the HTML map.
        map_path = session_dir / "tpr_distribution_map.html"
        map_path.write_text("<html>map</html>", encoding="utf-8")

        with patch("app.data_analysis_v3.tools.tpr_analysis_tool.analyze_tpr_data") as mock_tool:
            mock_tool.invoke.return_value = "Tool run complete.📍 TPR Map Visualization created."  # minimal stub

            result = handler.calculate_tpr()

        assert result["success"] is True
        assert result["visualizations"], "Visualization payload should not be empty"
        viz = result["visualizations"][0]
        assert viz["type"] == "iframe"
        assert viz["url"].endswith("tpr_distribution_map.html")
        assert "TestState" in viz["title"]
    finally:
        _cleanup_session(session_id)


def test_initialize_session_persists_dataset_metadata(flask_app, sample_dataset):
    session_id = "test-viz-persistence"
    try:
        with flask_app.app_context():
            initialize_tpr_session(session_id, sample_dataset)

        state_manager = DataAnalysisStateManager(session_id)
        dataset_path = state_manager.get_field("tpr_dataset_path")

        assert dataset_path
        assert Path(dataset_path).exists()
        assert state_manager.is_tpr_workflow_active() is True
        assert state_manager.get_field("csv_loaded") is True
    finally:
        _cleanup_session(session_id)
        shutil.rmtree(Path(flask_app.config["UPLOAD_FOLDER"]) / session_id, ignore_errors=True)
