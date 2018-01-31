import logging
import os
import json
import sys
import traceback

from invoicer import validate_schema, build_invoice, build_email
from aws.ses import send_email
from aws.cloudwatch_events import put_cloudwatch_rule, put_cloudwatch_target, delete_cloudwatch_rule, delete_cloudwatch_target

LOG = logging.getLogger(__name__)
LOG.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def api_handler(event, context):
    try:
        LOG.debug(event)
        request_path = event.get('path')
        request_type = event.get('httpMethod')
        request_parameters = event.get('pathParameters')
        requested_client_id = request_parameters.get('client_id') if request_parameters else None
        router = {
            'POST': {
                '/invoices': (send_invoice, event.get('body', event)),
                '/invoices/scheduled': (schedule_recurring_invoice, event.get('body', event))
            },
            'DELETE': {
                '/invoices/scheduled/{}'.format(requested_client_id): (unschedule_recurring_invoice, requested_client_id)
            }
        }
        handler, args = router[request_type][request_path]
        handler(args)
        return dict(
            statusCode=200
        )
    except Exception as e:
        LOG.error(e)
        traceback.print_exc(file=sys.stdout)
        return dict(
            statusCode=400,
            body=str(e)
        )

def unschedule_recurring_invoice(client_id):
        delete_cloudwatch_target(client_id)
        delete_cloudwatch_rule(client_id)

def schedule_recurring_invoice(invoice_string):
    invoice_config = json.loads(invoice_string)
    validate_schema(invoice_config)
    client_id = invoice_config['client_info']['client_id']
    schedule_expression = invoice_config.get('schedule_expression')
    if not schedule_expression:
        raise Exception('Please provide a schedule expression for this recurring invoice')
    
    put_cloudwatch_rule(client_id, schedule_expression)
    put_cloudwatch_target(client_id, json.dumps(invoice_config))

def send_invoice(invoice_string):
    invoice_config = json.loads(invoice_string)
    validate_schema(invoice_config)
    build_invoice(invoice_config)
    message = build_email(invoice_config)

    send_email(
        message,
        invoice_config['agreement_info']['provider_email'],
        invoice_config['agreement_info']['client_emails'],
        invoice_config['agreement_info'].get('verified_sender_arn')
    )