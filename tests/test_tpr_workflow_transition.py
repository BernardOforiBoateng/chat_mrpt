"""Runtime regression tests that focus on navigation and handler rehydration."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest
from flask import Flask

from app.data_analysis_v3.core.state_manager import ConversationStage
from app.runtime.tpr.workflow import (
    get_tpr_status,
    initialize_tpr_session,
    process_tpr_message,
    reset_tpr_handler_cache,
    start_tpr_workflow,
)


@pytest.fixture
def flask_app(tmp_path):
    app = Flask(__name__)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)
    with app.app_context():
        yield app


@pytest.fixture
def sample_tpr_dataframe():
    return pd.DataFrame(
        {
            "State": ["Adamawa", "Kwara", "Kwara"],
            "LGA": ["Yola", "Ilorin", "Offa"],
            "Ward": ["Ward 1", "Ward 2", "Ward 3"],
            "FacilityLevel": ["Primary", "Primary", "Secondary"],
            "Tested by RDT (Fever cases)": [100, 120, 90],
            "Positive for malaria by RDT": [20, 30, 18],
        }
    )


def _cleanup_session(base_dir: Path, session_id: str) -> None:
    reset_tpr_handler_cache(session_id)
    shutil.rmtree(base_dir / session_id, ignore_errors=True)
    shutil.rmtree(Path("instance/uploads") / session_id, ignore_errors=True)


def test_back_navigation_returns_to_state_selection(flask_app, sample_tpr_dataframe):
    session_id = "test-transition-back"
    base_dir = Path(flask_app.config["UPLOAD_FOLDER"])
    try:
        with flask_app.app_context():
            initialize_tpr_session(session_id, sample_tpr_dataframe)
        start_tpr_workflow(session_id)
        process_tpr_message(session_id, "Kwara")

        # Workflow should now be sitting at facility selection.
        status = get_tpr_status(session_id)
        assert status["stage"] == ConversationStage.TPR_FACILITY_LEVEL.value

        back_payload = process_tpr_message(session_id, "back")
        assert back_payload["stage"] == "state_selection"
        assert "let's go back" in back_payload["message"].lower()

        status_after = get_tpr_status(session_id)
        assert status_after["stage"] == ConversationStage.TPR_STATE_SELECTION.value
    finally:
        _cleanup_session(base_dir, session_id)


def test_handler_rehydrates_after_cache_clear(flask_app, sample_tpr_dataframe):
    session_id = "test-transition-rehydrate"
    base_dir = Path(flask_app.config["UPLOAD_FOLDER"])
    try:
        with flask_app.app_context():
            initialize_tpr_session(session_id, sample_tpr_dataframe)
        start_tpr_workflow(session_id)
        process_tpr_message(session_id, "Adamawa")  # advance to facility stage

        # Blow away handler cache to simulate worker restart.
        reset_tpr_handler_cache(session_id)

        # Navigation commands should still work after the handler is rebuilt.
        back_payload = process_tpr_message(session_id, "back")
        assert back_payload["stage"] == "state_selection"

        status_after = get_tpr_status(session_id)
        assert status_after["stage"] == ConversationStage.TPR_STATE_SELECTION.value
    finally:
        _cleanup_session(base_dir, session_id)
