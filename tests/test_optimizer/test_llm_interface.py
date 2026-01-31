# tests/test_optimizer/test_llm_interface.py
import pytest
from src.optimizer.llm_interface import LLMInterface


@pytest.fixture
def mock_deepseek_client(mocker):
    mock_chat = mocker.Mock()
    mock_chat.completions.create.return_value.choices = [
        mocker.Mock(message=mocker.Mock(content='{"param1": 10, "param2": "test"}'))
    ]
    mocker.patch(
        "src.optimizer.llm_interface.OpenAI", return_value=mocker.Mock(chat=mock_chat)
    )
    return mock_chat


@pytest.fixture
def llm_interface(test_config, monkeypatch, mock_deepseek_client):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy_key")
    return LLMInterface(test_config)


def test_query_llm_success(llm_interface, mock_deepseek_client):
    prompt = "Generate parameters"
    context = {"current_state": "normal"}
    result = llm_interface.query_llm(prompt, context)
    assert result == {"param1": 10, "param2": "test"}
    mock_deepseek_client.completions.create.assert_called_once()


def test_query_llm_no_api_key(test_config, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    llm_interface_no_key = LLMInterface(test_config)
    result = llm_interface_no_key.query_llm("prompt", {})
    assert result is None


def test_parse_json_response(llm_interface):
    json_string = '{"key": "value", "number": 123}'
    result = llm_interface.parse_json_response(json_string)
    assert result == {"key": "value", "number": 123}


def test_parse_json_response_invalid(llm_interface):
    invalid_json_string = '{"key": "value", "number": 123'
    result = llm_interface.parse_json_response(invalid_json_string)
    assert result is None
