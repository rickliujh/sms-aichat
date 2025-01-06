import os
import base64
import urllib.parse
from dacite import from_dict
from dataclasses import dataclass
from huggingface_hub import InferenceClient
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    LambdaFunctionUrlEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(service="sms-chat-handler")


class HTTPError(Exception):
    def __init__(self, code: int = 500):
        self.status_code = code


@dataclass
class TwilioWebhookRequest:
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
    apikey: str,
    acToken: str,
    webhook_url: str,
    data:str,
    validator: RequestValidator,
):
    if len(acSid) == 0 or len(apikey) == 0:
        logger.error("twilio AccountSid and/or Huggingface API key are missing")
        raise HTTPError()
    # if not validator.validate(
    #     webhook_url,
    #     data,
    #     acToken,
    # ):
    #     logger.error("authentication for Twilio failed")
    #     raise HTTPError(401)


def flatten_dict_of_arrays(d):
    flattened_dict = {}
    for key, value in d.items():
        if isinstance(value, list) and len(value) == 1:
            flattened_dict[key] = value[0]
        else:
            flattened_dict[key] = value
    return flattened_dict


def get_data(event: LambdaFunctionUrlEvent) -> TwilioWebhookRequest:
    parsed = flatten_dict_of_arrays(
        urllib.parse.parse_qs(
            base64.b64decode(event.body).decode("utf-8"), 
            keep_blank_values=True
        )
    )
    data = from_dict(TwilioWebhookRequest, parsed)
    return data


def get_prompt(event: LambdaFunctionUrlEvent) -> str:
    return get_data(event).Body


@event_source(data_class=LambdaFunctionUrlEvent)
def handler(event: LambdaFunctionUrlEvent, context: LambdaContext) -> dict | str:
    twilioAcSid = os.environ["TWILIO_ACCOUNTSID"]
    twilioToken = os.environ["TWILIO_TOKEN"]
    webhookVali = RequestValidator(twilioToken)
    hgfApiKey = os.environ["HGF_KEY"]
    client = InferenceClient(api_key=hgfApiKey)
    logger.debug("prompt payload: ", extra={"event": (event), "context": context})

    try:
        webhook_url = f"https://{event.request_context.domain_name}/{event.path}"
        verify(twilioAcSid, hgfApiKey, twilioToken, webhook_url, event.body, webhookVali)

        req_data = get_data(event)
        prompt = get_prompt(event)

        logger.append_keys(message_id=req_data.MessageSid)
        logger.info("prompt incoming")
        logger.debug("prompt payload: ", extra={"event": (event), "context": context})

        resp = MessagingResponse()
        if prompt is None:
            resp.message("No prompt found.")
            logger.info("request without a prompt.", extra={"event": event})
            return str(resp)

        messages = [{"role": "user", "content": prompt}]

        logger.debug("calling inference", extra={"prompt": messages})

        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.2-1B-Instruct", messages=messages, max_tokens=500
        )

        logger.debug("inferencce response", extra={"response": completion})

        logger.info("sending response to use after inferencce completed")

        resp.message(completion.choices[0].message.content)

        return str(resp)
    except HTTPError as err:
        return {"statusCode": err.status_code}
