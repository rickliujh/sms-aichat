import os
from huggingface_hub import InferenceClient
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import event_source, ALBEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


class HTTPError(Exception):
    def __init__(self, code: int = 500):
        self.status_code = code


def verify(
    acSid: str, apikey: str, acToken: str, event: ALBEvent, validator: RequestValidator
):
    if len(acSid) == 0 or len(apikey) == 0:
        logger.error("twilio AccountSid and/or Huggingface API key are missing")
        raise HTTPError()
    if not validator.validate(
        event.path,
        event.body,
        acToken,
    ):
        logger.error("authentication for Twilio failed")
        raise HTTPError(401)


def get_prompt(event: ALBEvent) -> str:
    return event.body["prompt"]  # type: ignore


@event_source(data_class=ALBEvent)
def handler(event: ALBEvent, context: LambdaContext) -> dict | str:
    twilioAcSid = os.environ["TWILIO_ACCOUNTSID"]
    twilioToken = os.environ["TWILIO_TOKEN"]
    webhookVali = RequestValidator(twilioToken)
    hgfApiKey = os.environ["HGF_KEY"]
    client = InferenceClient(api_key=hgfApiKey)

    try:
        verify(twilioAcSid, hgfApiKey, twilioToken, event, webhookVali)

        logger.info("prompt incoming")
        logger.debug("prompt payload: ", extra={"event": (event), "context": context})

        resp = MessagingResponse()
        prompt = get_prompt(event)
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
