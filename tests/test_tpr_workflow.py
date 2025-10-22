"""Runtime-oriented tests for the TPR workflow interface."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest
from flask import Flask

from app.data_analysis_v3.core.state_manager import ConversationStage, DataAnalysisStateManager
from app.runtime.tpr.workflow import (
    cancel_tpr_workflow,
    get_tpr_status,
    initialize_tpr_session,
    process_tpr_message,
    reset_tpr_handler_cache,
    start_tpr_workflow,
)


@pytest.fixture
def flask_app(tmp_path):
    """Provide a minimal Flask app so UploadService uses an isolated directory."""

    app = Flask(__name__)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)

    with app.app_context():
        yield app


@pytest.fixture
def sample_tpr_dataframe():
    """Create a tiny dataset with multiple states to exercise the workflow."""

    return pd.DataFrame(
        {
            "State": ["Adamawa", "Adamawa", "Kwara", "Kwara"],
            "LGA": ["Yola", "Girei", "Ilorin", "Offa"],
            "WardName": ["Ward 1", "Ward 2", "Ward 3", "Ward 4"],
            "FacilityLevel": ["Primary", "Secondary", "Primary", "Tertiary"],
            "Tested by RDT (Fever cases)": [120, 80, 150, 95],
            "Positive for malaria by RDT": [30, 20, 45, 18],
            "Tested by Microscopy (Fever cases)": [60, 40, 70, 25],
            "Positive for malaria by Microscopy": [15, 8, 20, 6],
        }
    )


def _cleanup_session(base_dir: Path, session_id: str) -> None:
    reset_tpr_handler_cache(session_id)
    shutil.rmtree(base_dir / session_id, ignore_errors=True)
    shutil.rmtree(Path("instance/uploads") / session_id, ignore_errors=True)


def test_runtime_flow_progression(flask_app, sample_tpr_dataframe):
    """TPR runtime helpers should persist data and advance through state selection."""

    session_id = "test-runtime-flow"
    base_dir = Path(flask_app.config["UPLOAD_FOLDER"])
    try:
        with flask_app.app_context():
            initialize_tpr_session(session_id, sample_tpr_dataframe)

        # Dataset gets persisted so a fresh handler can restore it later.
        session_dir = base_dir / session_id
        assert (session_dir / "raw_data.csv").exists()
        assert (session_dir / "data_analysis.csv").exists()

        # Kick off the workflow – multiple states should keep us in state-selection stage.
        start_payload = start_tpr_workflow(session_id)
        assert start_payload["workflow"] == "tpr"
        assert start_payload["stage"] == "state_selection"

        # User picks a state; handler should advance to facility selection and memoise choice.
        message_payload = process_tpr_message(session_id, "Adamawa")
        assert message_payload["success"] is True
        assert message_payload["stage"] == "facility_selection"

        status = get_tpr_status(session_id)
        assert status["selections"]["state"] in {"Adamawa", "adamawa"}
        assert status["stage"] == ConversationStage.TPR_FACILITY_LEVEL.value
    finally:
        _cleanup_session(base_dir, session_id)


def test_cancel_workflow_clears_state(flask_app, sample_tpr_dataframe):
    """Cancelling from the runtime wrapper clears state manager flags."""

    session_id = "test-runtime-cancel"
    base_dir = Path(flask_app.config["UPLOAD_FOLDER"])
    try:
        with flask_app.app_context():
            initialize_tpr_session(session_id, sample_tpr_dataframe)
        start_tpr_workflow(session_id)
        process_tpr_message(session_id, "Adamawa")

        # Confirm workflow shows as active before cancellation.
        status_before = get_tpr_status(session_id)
        assert status_before["active"] is True

        cancel_response = cancel_tpr_workflow(session_id)
        assert cancel_response["status"] == "success"

        state_manager = DataAnalysisStateManager(session_id)
        assert state_manager.is_tpr_workflow_active() is False
        assert state_manager.get_tpr_selections() == {}

        status_after = get_tpr_status(session_id)
        assert status_after["active"] is False
        assert status_after["selections"] == {}
    finally:
        _cleanup_session(base_dir, session_id)


def test_process_unknown_input_returns_fallback(flask_app, sample_tpr_dataframe):
    """Unknown inputs should yield a graceful fallback payload instead of exceptions."""

    session_id = "test-runtime-fallback"
    base_dir = Path(flask_app.config["UPLOAD_FOLDER"])
    try:
        with flask_app.app_context():
            initialize_tpr_session(session_id, sample_tpr_dataframe)
        start_tpr_workflow(session_id)

        response = process_tpr_message(session_id, "this is not valid")
        assert response["workflow"] == "tpr"
        assert response["success"] is True
        assert response.get("stage") in {"state_selection", "facility_selection"}
        assert "facility" in response["message"].lower()
    finally:
        _cleanup_session(base_dir, session_id)
