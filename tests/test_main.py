import pytest
from models import Base, History
from main import save_to_history, fetch_history, call_llm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

@pytest.fixture(scope="module")
def test_session():
    # Setup in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session
    session.close()

def test_save_to_history(test_session):
    with patch("main.Session", return_value=test_session):  # Patch the session
        save_to_history("Add 2 and 3", "5")
        result = test_session.query(History).filter_by(user_input="Add 2 and 3").first()
        assert result is not None
        assert result.result == "5"

def test_fetch_history(test_session, capsys):
    with patch("main.Session", return_value=test_session):  # Patch the session
        save_to_history("Multiply 3 and 4", "12")
        fetch_history()
        captured = capsys.readouterr()
        assert "Input: Multiply 3 and 4" in captured.out
        assert "Output: 12" in captured.out

def test_call_llm(monkeypatch):
    # Mock the response from the API
    def mock_call_llm(prompt):
        return 8  # Mock result for testing purposes

    # Monkeypatch the `call_llm` function in `main.py`
    monkeypatch.setattr("main.call_llm", mock_call_llm)

    # Call the mocked function
    result = call_llm("Add 5 and 3")
    assert result == 8

