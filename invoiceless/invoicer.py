from datetime import datetime, timedelta

import logging
import os

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from pyinvoice.models import InvoiceInfo, ServiceProviderInfo, ClientInfo, Item
from pyinvoice.templates import SimpleInvoice
import jsonschema

LOG = logging.getLogger(__name__)
LOG.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

PDF_PATH = '/tmp/invoice.pdf'

SCHEMA = {
    "type": "object",
    "properties": {
        "schedule_expression": {
            "type": "string"
        },
        "service_provider_info": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "street": {
                    "type": "string"
                },
                "city": {
                    "type": "string"
                },
                "state": {
                    "type": "string"
                },
                "country": {
                    "type": "string"
                },
                "post_code": {
                    "type": "string"
                }
            },
            "required": ["name"]
        },
        "client_info": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                },
                "street": {
                    "type": "string"
                },
                "city": {
                    "type": "string"
                },
                "state": {
                    "type": "string"
                },
                "country": {
                    "type": "string"
                },
                "post_code": {
                    "type": "string"
                }
            },
            "required": ["client_id", "name"]
        },
        "agreement_info": {
            "type": "object",
            "properties": {           
                "net": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 120
                },
                "client_emails": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "uniqueItems": True
                },
                "provider_email": {
                    "type": "string"
                },
                "verified_sender_arn":
                {
                   "type": "string" 
                }
            },
            "required": ["client_emails", "provider_email"]
        },
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                    "units": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "unit_price": {
                        "type": "number",
                        "minimum": 0.01
                    }
                },
                "required": ["name", "units", "unit_price"]
            }
        }
    },
    "required": ["agreement_info", "service_provider_info", "client_info", "line_items"]
}

def validate_schema(invoice):
    validator = jsonschema.Draft4Validator(SCHEMA)
    errors = sorted(validator.iter_errors(invoice), key=lambda e: e.path)
    if errors:
        raise Exception("Invalid invoice format: {}".format(errors))

def get_invoice_number(client_id):
    return int(client_id + str(datetime.now().year) + str(datetime.now().month))

def build_invoice(invoice_config):
    net = invoice_config['agreement_info'].get('net', 30)
    invoice_number = get_invoice_number(invoice_config['client_info']['client_id'])
    
    doc = SimpleInvoice(PDF_PATH)
    doc.invoice_info = InvoiceInfo(invoice_number, datetime.now(), datetime.now() + timedelta(days=net))
    doc.service_provider_info = ServiceProviderInfo(**invoice_config['service_provider_info'])
    doc.client_info = ClientInfo(**invoice_config['client_info'])

    for item in invoice_config['line_items']:
        doc.add_item(Item(**item))
    
    doc.set_bottom_tip("Thanks for your business!<br />Email: {}<br />Don't hesitate to contact us for any questions.".format(invoice_config['agreement_info']['provider_email']))

    doc.finish()

def build_email(invoice_config):
    msg = MIMEMultipart()
    msg['Subject'] = 'Invoice - ' + str(get_invoice_number(invoice_config['client_info']['client_id']))
    msg['From'] = "{} <{}>".format(invoice_config['service_provider_info']['name'], invoice_config['agreement_info']['provider_email'])
    msg['To'] = ", ".join(invoice_config['agreement_info']['client_emails'])

    msg.preamble = 'Your monthly invoice is attached.\n'
    part = MIMEText('Hi -- please find attached your monthly invoice.')
    msg.attach(part)

    part = MIMEApplication(open(PDF_PATH, 'rb').read())
    part.add_header('Content-Disposition', 'attachment', filename='invoice.pdf')
    msg.attach(part)

    return msg
   