import base64
import urllib.parse
from dacite import from_dict
from dataclasses import dataclass
from huggingface_hub import InferenceClient
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from aws_lambda_powertools.utilities.data_classes import (
    LambdaFunctionUrlEvent,
)


class HTTPError(Exception):
    def __init__(self, msg: str = "Server error", code: int = 500):
        self.message = msg
        self.status_code = code


@dataclass
class TwilioRequestFormData:
    ToCountry: str | None
    ToState: str | None
    SmsMessageSid: str | None
    NumMedia: str | None
    ToCity: str | None
    FromZip: str | None
    SmsSid: str | None
    FromState: str | None
    SmsStatus: str | None
    FromCity: str | None
    Body: str
    FromCountry: str | None
    To: str
    ToZip: str | None
    NumSegments: str | None
    MessageSid: str
    AccountSid: str
    From: str
    ApiVersion: str


def verify(
    acSid: str,
    llm_api_key: str,
    event: LambdaFunctionUrlEvent,
    validator: RequestValidator,
):
    webhook_url = f"https://{event.request_context.domain_name}{event.path}"
    data = parse_form_data(event)
    req_sig = event.headers.get("X-Twilio-Signature")

    if len(acSid) == 0 or len(llm_api_key) == 0:
        raise HTTPError(msg="twilio AccountSid and/or Huggingface API key are missing")
    if not validator.validate(
        webhook_url,
        data.__dict__,
        req_sig,
    ):
        raise HTTPError(msg="authentication for Twilio failed", code=401)


def flatten_dict_of_arrays(d):
    flattened_dict = {}
    for key, value in d.items():
        if isinstance(value, list) and len(value) == 1:
            flattened_dict[key] = value[0]
        else:
            flattened_dict[key] = value
    return flattened_dict


def parse_form_data(event: LambdaFunctionUrlEvent) -> TwilioRequestFormData:
    try:
        parsed = flatten_dict_of_arrays(
            urllib.parse.parse_qs(
                base64.b64decode(event.body).decode("utf-8"),  # type: ignore
                keep_blank_values=True,
            )
        )
        data = from_dict(TwilioRequestFormData, parsed)
        return data
    except Exception:
        return None  # type: ignore


def prompt(event: LambdaFunctionUrlEvent) -> str | None:
    try:
        return parse_form_data(event).Body
    except AttributeError:
        return None


def infer(event: LambdaFunctionUrlEvent, client: InferenceClient, model: str) -> str:
    data = prompt(event)

    if data is None:
        return "No prompt found."

    messages = [{"role": "user", "content": data}]

    completion = client.chat.completions.create(
        model=model, messages=messages, max_tokens=500
    )

    return completion.choices[0].message.content


def pack_resp(data: str) -> str:
    resp = MessagingResponse()
    resp.message(data)
    return str(resp)
