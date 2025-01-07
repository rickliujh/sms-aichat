import os
from huggingface_hub import InferenceClient
from twilio.request_validator import RequestValidator
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    LambdaFunctionUrlEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from sms_aichat import verify, infer, pack_resp, parse_form_data, HTTPError

LLM_MODEL = "meta-llama/Llama-3.2-1B-Instruct"

twilioAcSid = os.environ["TWILIO_ACCOUNTSID"]
twilioToken = os.environ["TWILIO_TOKEN"]
webhookVali = RequestValidator(twilioToken)
hgfApiKey = os.environ["HGF_KEY"]
logger = Logger(service="sms-chat-handler")
client = InferenceClient(api_key=hgfApiKey)


@event_source(data_class=LambdaFunctionUrlEvent)
def handler(event: LambdaFunctionUrlEvent, context: LambdaContext) -> dict | str:
    try:
        req_data = parse_form_data(event)
        logger.append_keys(message_id=req_data.MessageSid)
        logger.info("excecting webhook")
        logger.debug("request payload", extra={"event": (event), "context": context})

        verify(twilioAcSid, hgfApiKey, event, webhookVali)

        logger.debug("start inference")
        data = infer(event, client, LLM_MODEL)
        logger.debug("inferencce result", extra={"data": data})

        resp = {
            "statusCode": 200,
            "headers": {"Content-Type": "text/xml"},
            "body": pack_resp(data),
        }
        logger.debug("response generated", extra=resp)

        return resp
    except HTTPError as err:
        logger.error("request invalid", err)
        return {"statusCode": err.status_code}
