"""Streamlit interaction tests. No network or cloud accounts required."""
from pathlib import Path
import io
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'

def test_initial_render_and_offline_answer():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert [m.value for m in app.metric] == ['200', '1', '1']
    app.button[0].click().run()
    assert not app.exception and not app.error
    result = app.session_state['result']
    assert result['revenue'].sum() == 98108.25

def test_unsupported_question_is_visible_error():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.text_input[0].set_value('invent a forecast').run()
    app.button[0].click().run()
    assert not app.exception
    assert 'Offline demo supports' in app.error[0].value
    assert 'result' not in app.session_state

def test_model_evaluation_renders_metrics():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.button[1].click().run()
    assert not app.exception and not app.error
    assert any('baseline_mae' in item.value for item in app.json)

def test_missing_ai_config_is_actionable(monkeypatch):
    monkeypatch.delenv('LLM_MODEL', raising=False)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.toggle[0].set_value(True).run()
    app.button[0].click().run()
    assert not app.exception
    assert 'Set LLM_MODEL' in app.error[0].value

def test_uploaded_dataset_change_clears_previous_answer(monkeypatch):
    import streamlit
    current = [b'a\n1\n2\n']
    monkeypatch.setattr(streamlit, 'file_uploader', lambda *a, **kw: io.BytesIO(current[0]))
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.text_input[0].set_value('How many rows?').run()
    app.button[0].click().run()
    assert app.session_state['result'].iloc[0, 0] == 2
    current[0] = b'a\n7\n8\n9\n'
    app.run()
    assert not app.exception
    assert 'result' not in app.session_state
    assert app.metric[0].value == '3'

def test_empty_upload_shows_error_instead_of_crashing(monkeypatch):
    import streamlit
    monkeypatch.setattr(streamlit, 'file_uploader', lambda *a, **kw: io.BytesIO(b'a\n'))
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert 'Use 1' in app.error[0].value
