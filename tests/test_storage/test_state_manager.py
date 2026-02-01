# tests/test_storage/test_state_manager.py
import os

import pytest
from storage.state_manager import StateManager


@pytest.fixture
def state_manager_file(test_config, tmp_path):
    # Use a temporary file for the database to ensure isolation
    db_file = tmp_path / "test_optimizer_state.db"
    test_config["system_config"]["paths"]["state_db"] = str(db_file)
    sm = StateManager(test_config)
    yield sm
    os.remove(db_file)  # Clean up after test


def test_initialize_db(state_manager_file):
    # The fixture already initializes the DB
    assert os.path.exists(state_manager_file.db_path)


def test_execute_query_insert_and_fetch(state_manager_file):
    state_manager_file.execute_query(
        "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT);"
    )
    state_manager_file.execute_query(
        "INSERT INTO test_table (name) VALUES (?);", ("test_name_1",)
    )
    state_manager_file.execute_query(
        "INSERT INTO test_table (name) VALUES (?);", ("test_name_2",)
    )

    result_one = state_manager_file.execute_query(
        "SELECT name FROM test_table WHERE id = 1;", fetch="one"
    )
    assert result_one == ("test_name_1",)

    result_all = state_manager_file.execute_query(
        "SELECT name FROM test_table;", fetch="all"
    )
    assert result_all == [("test_name_1",), ("test_name_2",)]


def test_save_and_load_state(state_manager_file):
    state_manager_file.save_state("test_key", "test_value")
    loaded_value = state_manager_file.load_state("test_key")
    assert loaded_value == "test_value"


def test_load_non_existent_state(state_manager_file):
    loaded_value = state_manager_file.load_state("non_existent_key")
    assert loaded_value is None


def test_replace_state(state_manager_file):
    state_manager_file.save_state("test_key", "initial_value")
    state_manager_file.save_state("test_key", "updated_value")
    loaded_value = state_manager_file.load_state("test_key")
    assert loaded_value == "updated_value"
