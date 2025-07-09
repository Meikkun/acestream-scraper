import os
import tempfile
import shutil
from app.utils import path

def test_config_dir_local(monkeypatch):
    monkeypatch.delenv('DOCKER_ENVIRONMENT', raising=False)
    config_path = path.config_dir()
    assert config_path.exists()
    assert 'config' in str(config_path)

def test_log_dir_local(monkeypatch):
    monkeypatch.delenv('DOCKER_ENVIRONMENT', raising=False)
    log_path = path.log_dir()
    assert log_path.exists()
    assert 'logs' in str(log_path)

def test_config_dir_docker(monkeypatch):
    monkeypatch.setenv('DOCKER_ENVIRONMENT', '1')
    config_path = path.config_dir()
    assert config_path.as_posix() == '/config'

def test_log_dir_docker(monkeypatch):
    monkeypatch.setenv('DOCKER_ENVIRONMENT', '1')
    log_path = path.log_dir()
    assert log_path.as_posix() == '/config/logs'

def test_get_database_path(monkeypatch):
    monkeypatch.delenv('DOCKER_ENVIRONMENT', raising=False)
    db_path = path.get_database_path()
    assert db_path.name == 'acestream.db'
    assert 'config' in str(db_path)
