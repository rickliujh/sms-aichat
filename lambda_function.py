import os
from aws_lambda_powertools import Logger
from huggingface_hub import InferenceClient
from twilio.twiml.messaging_response import MessagingResponse
from aws_lambda_powertools.utilities.data_classes import ALBEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
twilioAcSid = os.environ["TWILIO_ACCOUNTSID"]
hgfApiKey=os.environ["HGF_KEY"]
client = InferenceClient(api_key=hgfApiKey)

def verify(acSid: string, apikey: string):
    if len(acSid) is 0 or len(apikey) is 0:
        raise Exception("Twilio AccountSid and/or Huggingface API key are missing")

def handler(event: ALBEvent, context: LambdaContext):
    verify(twilioAcSid, hgfApiKey)

    logger.info("prompt incoming")
    logger.debug("prompt payload: ", extra={"event": event, "context": context})

    resp = MessagingResponse()

    messages = [
        {
            "role": "user",
            "content": event["prompt"],
        }
    ]

    logger.debug("calling inference", extra={"prompt": messages})

    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.2-1B-Instruct", messages=messages, max_tokens=500
    )

    logger.debug("inferencce response", extra={"response": completion})

    logger.info("sending response to use after inferencce completed")

    resp.message(completion.choices[0].message.content)

    return str(resp)
