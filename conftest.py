# conftest.py
import pytest
import database
import routes
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from app import app as flask_app

TEST_DB = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)

@pytest.fixture(scope="function")
def db(engine):
    Session = sessionmaker(bind=engine)
    sesion = Session()
    # Reemplazamos SessionLocal globalmente para que las rutas usen esta sesión
    original = database.SessionLocal
    database.SessionLocal = lambda: sesion
    routes.SessionLocal   = lambda: sesion
    yield sesion
    database.SessionLocal = original
    routes.SessionLocal   = original
    sesion.rollback()
    sesion.close()

@pytest.fixture(scope="function")
def client(db):
    flask_app.config["TESTING"]          = True
    flask_app.config["SECRET_KEY"]       = "test_key"
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as c:
        yield c

@pytest.fixture(scope="function")
def client_admin(client):
    with client.session_transaction() as sess:
        sess["usuario_id"] = 1
        sess["nombre"]     = "Admin Test"
        sess["rol"]        = "admin"
    return client

@pytest.fixture(scope="function")
def client_cajero(client):
    with client.session_transaction() as sess:
        sess["usuario_id"] = 2
        sess["nombre"]     = "Cajero Test"
        sess["rol"]        = "cajero"
    return client