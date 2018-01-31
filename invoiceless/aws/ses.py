import boto3
import logging
import os

LOG = logging.getLogger(__name__)
LOG.setLevel(os.environ.get('LogLevel', 'INFO'))

SES_CLIENT = boto3.client('ses')

def send_email(mime_msg, source, destinations, verified_sender_arn=None):
    response = SES_CLIENT.send_raw_email(
        RawMessage={
            'Data': mime_msg.as_string()
        },
        Source=source,
        Destinations=destinations,
        SourceArn=verified_sender_arn
    )
    LOG.debug(response)