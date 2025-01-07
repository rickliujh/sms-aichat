import sys
import os
import json
import pytest
from unittest.mock import Mock
from aws_lambda_powertools.utilities.data_classes import LambdaFunctionUrlEvent
from twilio.request_validator import RequestValidator

sys.path.append(os.path.curdir + "/src")
from sms_aichat import (
    verify,
    parse_form_data,
    prompt,
    infer,
    pack_resp,
    HTTPError,
    TwilioRequestFormData,
)


def snake_to_camel(snake_str):
    parts = snake_str.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def transform_keys(data):
    if isinstance(data, dict):
        return {
            snake_to_camel(key): transform_keys(value) for key, value in data.items()
        }
    elif isinstance(data, list):
        return [transform_keys(item) for item in data]
    else:
        return data


def load_sample_event_from_file(test_event_file_name: str) -> dict:
    event_file_name = f"tests/events/{test_event_file_name}.json"
    with open(event_file_name, "r", encoding="UTF-8") as file_handle:
        event = json.load(file_handle)
        # validate(event=event, schema=INPUT)
        return transform_keys(event)


def test_verify_httperror_500() -> None:
    acSid = ""
    apikey = ""
    event = LambdaFunctionUrlEvent(load_sample_event_from_file("testEvent1"))
    with pytest.raises(HTTPError) as err:
        verify(acSid, apikey, event, None)
    assert err.value.status_code == 500


def test_verify_httperror_401() -> None:
    acSid = "fack account"
    apikey = "fake key"
    twilioToken = "fake token"

    print(twilioToken)
    event = LambdaFunctionUrlEvent(load_sample_event_from_file("testEvent1"))
    validator = RequestValidator(twilioToken)

    with pytest.raises(HTTPError) as err:
        verify(acSid, apikey, event, validator)
    assert err.value.status_code == 401


def test_parse_from_data() -> None:
    event = LambdaFunctionUrlEvent(load_sample_event_from_file("testEvent1"))
    data = parse_form_data(event)
    assert isinstance(data, TwilioRequestFormData)
    assert data == TwilioRequestFormData(
        ToCountry="US",
        ToState="CA",
        SmsMessageSid="SM6c7d4hm7aftesttest7396392b4658d2",
        NumMedia="0",
        ToCity="San Francisco",
        FromZip="",
        SmsSid="SM6c7d4hm7aftesttest7396392b4658d2",
        FromState="",
        SmsStatus="received",
        FromCity="",
        Body="What is the capital of France?",
        FromCountry="US",
        To="+16282234100",
        ToZip="",
        NumSegments="1",
        MessageSid="SM6c7d4hm7aftesttest7396392b4658d2",
        AccountSid="ACcabc52fafatesttest6fb0171",
        From="+1873423153",
        ApiVersion="2010-04-01",
    )


def test_prompt() -> None:
    event = LambdaFunctionUrlEvent(load_sample_event_from_file("testEvent1"))
    assert prompt(event) == "What is the capital of France?"


def get_mock_client(msg: str):
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()

    mock_return = Mock()
    mock_return.choices = [Mock(message=Mock(content=msg))]
    mock_client.chat.completions.create.return_value = mock_return

    return mock_client


def test_infer_general() -> None:
    event = LambdaFunctionUrlEvent(load_sample_event_from_file("testEvent1"))
    mock_client = get_mock_client("The capital of France is Paris.")
    model = "any model"

    assert infer(event, mock_client, model) == "The capital of France is Paris."
    mock_client.chat.completions.create.assert_called_once_with(
        model=model,
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        max_tokens=500,
    )


def test_infer_no_prompt() -> None:
    mock_event = Mock(body="")
    mock_client = get_mock_client("The capital of France is Paris.")
    assert infer(mock_event, mock_client, "") == "No prompt found."


def test_pack_resp() -> None:
    assert (
        pack_resp("hello world!")
        == '<?xml version="1.0" encoding="UTF-8"?><Response><Message>hello world!</Message></Response>'
    )
