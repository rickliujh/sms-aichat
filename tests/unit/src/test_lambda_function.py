import sys
import os
import json
import pytest
from dotenv import load_dotenv
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.data_classes import ALBEvent
from twilio.request_validator import RequestValidator
from huggingface_hub import InferenceClient

sys.path.append(os.path.curdir + "/src")
from lambda_function import handler, verify, get_prompt, HTTPError
from schemas import INPUT


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv(dotenv_path=os.path.curdir + "/.env")


def load_sample_event_from_file(test_event_file_name: str) -> dict:
    event_file_name = f"tests/events/{test_event_file_name}.json"
    with open(event_file_name, "r", encoding="UTF-8") as file_handle:
        event = json.load(file_handle)
        validate(event=event, schema=INPUT)
        return event


def test_verify_httperror_500() -> None:
    acSid = ""
    apikey = ""
    acToken = ""
    event = load_sample_event_from_file("testEvent1")
    with pytest.raises(HTTPError) as err:
        verify(acSid, apikey, acToken, ALBEvent(event), None)
    assert err.value.status_code == 500


def test_verify_httperror_401() -> None:
    acSid = "test"
    apikey = "test"
    acToken = ""
    event = load_sample_event_from_file("testEvent1")
    twilioToken = os.environ["TWILIO_TOKEN"]
    validator = RequestValidator(twilioToken)
    with pytest.raises(HTTPError) as err:
        verify(acSid, apikey, acToken, ALBEvent(event), validator)
    assert err.value.status_code == 401


def test_get_prompt() -> None:
    event = load_sample_event_from_file("testEvent1")
    assert get_prompt(ALBEvent(event)) == "What is the capital of France?"


class MockHGFChat:
    def __init__(self):
        self.completions = MockCompletions()


class MockCompletions:
    def create(self, *args, **kwargs):
        return MockResponse()


class MockResponse:
    def __init__(self):
        self.choices = [MockResponseMessage()]


class MockResponseMessage:
    def __init__(self):
        self.message = MockResponseMessageContent()


class MockResponseMessageContent:
    def __init__(self):
        self.content = "The capital of France is Paris."


def test_handler(monkeypatch) -> None:
    monkeypatch.setattr("lambda_function.verify", lambda *args: None)
    monkeypatch.setattr(InferenceClient, "chat", MockHGFChat(), raising=False)
    event = load_sample_event_from_file("testEvent1")
    assert (
        handler(event=event, context=None)
        == '<?xml version="1.0" encoding="UTF-8"?><Response><Message>The capital of France is Paris.</Message></Response>'
    )
