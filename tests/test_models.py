import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, History
from faker import Faker

# Setup in-memory SQLite database for testing
@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    # Seed the database with fake users
    fake = Faker()
    for _ in range(30):  # Generate 30 fake users
        user = User(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            username=fake.unique.user_name()
        )
        session.add(user)
    session.commit()

    yield session
    session.close()

def test_user_model(test_db):
    # Verify that 30 users are added
    users = test_db.query(User).all()
    assert len(users) == 30

    # Check the first user's structure
    first_user = users[0]
    assert first_user.first_name is not None
    assert first_user.last_name is not None
    assert "@" in first_user.email  # Ensure email looks valid
    assert first_user.username is not None

def test_history_model(test_db):
    # Test adding history records
    history_entry = History(
        user_input="Add 5 and 10",
        result="15"
    )
    test_db.add(history_entry)
    test_db.commit()

    # Verify the history entry
    fetched_entry = test_db.query(History).filter_by(user_input="Add 5 and 10").first()
    assert fetched_entry is not None
    assert fetched_entry.result == "15"
