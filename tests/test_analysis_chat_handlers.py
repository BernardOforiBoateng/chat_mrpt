import json
from types import SimpleNamespace

import pytest
from flask import Flask
from app.core.analysis_routes import analysis_bp
from unittest.mock import Mock

@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY='test-secret-key')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.services = SimpleNamespace(request_interpreter=None, interaction_logger=None)
    with app.app_context():
        yield app

@pytest.fixture
def configure_services(app_context):
    services = getattr(app_context, 'services', None)
    if services is None:
        services = SimpleNamespace(request_interpreter=None, interaction_logger=None)
        app_context.services = services
    return services


def _set_session(client, **values):
    with client.session_transaction() as sess:
        for key, value in values.items():
            sess[key] = value


def test_send_message_routes_to_tools(client, app_context, configure_services, monkeypatch):
    services = configure_services

    async def fake_route(message, session_context):
        return 'needs_tools'

    monkeypatch.setattr(
        'app.core.analysis_routes.chat.handlers.route_with_mistral',
        fake_route,
    )

    mock_interpreter = Mock()
    mock_interpreter.process_message.return_value = {
        'status': 'success',
        'response': 'Processed with tools',
        'tools_used': ['run_complete_analysis'],
    }
    services.request_interpreter = mock_interpreter

    _set_session(
        client,
        session_id='test-session-tools',
        csv_loaded=True,
        message_count=0,
    )

    response = client.post(
        '/analysis/send_message',
        json={'message': 'Please run the analysis', 'is_data_analysis': True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status'] == 'success'
    assert payload['response'] == 'Processed with tools'
    assert payload['tools_used'] == ['run_complete_analysis']

    mock_interpreter.process_message.assert_called_once()
    args, kwargs = mock_interpreter.process_message.call_args
    assert args[0] == 'Please run the analysis'
    assert kwargs['is_data_analysis'] is True


def test_send_message_routes_to_arena(client, app_context, configure_services, monkeypatch):
    services = configure_services
    services.request_interpreter = Mock()

    async def fake_route(message, session_context):
        return 'can_answer'

    monkeypatch.setattr(
        'app.core.analysis_routes.chat.handlers.route_with_mistral',
        fake_route,
    )

    def fake_arena_message(**kwargs):
        return (
            {
                'status': 'success',
                'arena_mode': True,
                'response': 'Arena comparison ready',
                'response_a': 'A',
                'response_b': 'B',
                'latency_a': 10,
                'latency_b': 12,
                'battle_id': 'battle-123',
                'view_index': 0,
                'model_a': 'model_a',
                'model_b': 'model_b',
            },
            None,
        )

    monkeypatch.setattr(
        'app.core.analysis_routes.chat.handlers.process_arena_message',
        lambda **kwargs: fake_arena_message(**kwargs),
    )

    _set_session(client, session_id='test-session-arena', message_count=0)

    response = client.post(
        '/analysis/send_message',
        json={'message': 'Hi there'},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['arena_mode'] is True
    assert data['battle_id'] == 'battle-123'
    services.request_interpreter.process_message.assert_not_called()


def test_send_message_returns_clarification_prompt(client, app_context, configure_services, monkeypatch):
    services = configure_services
    services.request_interpreter = Mock()

    async def fake_route(message, session_context):
        return 'needs_clarification'

    monkeypatch.setattr(
        'app.core.analysis_routes.chat.handlers.route_with_mistral',
        fake_route,
    )

    _set_session(client, session_id='clarify-session', message_count=0)

    response = client.post(
        '/analysis/send_message',
        json={'message': 'Need more details about risk levels'},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['needs_clarification'] is True

    with client.session_transaction() as sess:
        assert 'pending_clarification' in sess


def test_send_message_streaming_tools_path(client, app_context, configure_services, monkeypatch):
    services = configure_services

    async def fake_route(message, session_context):
        return 'needs_tools'

    monkeypatch.setattr(
        'app.core.analysis_routes.chat.handlers.route_with_mistral',
        fake_route,
    )

    def fake_stream(message, session_id=None, session_data=None):
        yield {'content': 'chunk-1', 'done': False}
        yield {'content': 'chunk-2', 'done': True}

    mock_interpreter = Mock()
    mock_interpreter.process_message_streaming.side_effect = fake_stream
    services.request_interpreter = mock_interpreter

    _set_session(client, session_id='stream-session', message_count=0)

    response = client.post(
        '/analysis/send_message_streaming',
        json={'message': 'Stream this'},
    )

    assert response.status_code == 200
    body = b''.join(response.response)
    # SSE chunks start with "data: " prefix
    assert b'data: {"content": "chunk-1"' in body
    assert b'data: {"content": "chunk-2"' in body

    mock_interpreter.process_message_streaming.assert_called_once()
