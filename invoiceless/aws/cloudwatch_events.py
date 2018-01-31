import os
import logging
import json

import boto3

LOG = logging.getLogger(__name__)
LOG.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

CLOUDWATCH_EVENTS_CLIENT = boto3.client('events')

def rule_name_formatter(name):
    return 'invoiceless-recurring-{}'.format(name)

def put_cloudwatch_rule(name, schedule):
    response = CLOUDWATCH_EVENTS_CLIENT.list_rules(
        NamePrefix=rule_name_formatter(name)
    )
    if response['Rules']:
        raise Exception('There is already a recurring invoice scheduled for this client! Please unschedule the existing invoice before creating a new one.')

    response = CLOUDWATCH_EVENTS_CLIENT.put_rule(
        Name=rule_name_formatter(name),
        ScheduleExpression=schedule,
        State='ENABLED',
        Description='Recurring Invoices for Client',
        RoleArn=os.environ.get('EVENT_ROLE')
    )
    LOG.debug(response)

def put_cloudwatch_target(name, input_body):
    input_object = {
        "path": "/invoices",
        "httpMethod": "POST",
        "body": input_body
    }
    response = CLOUDWATCH_EVENTS_CLIENT.put_targets(
        Rule=rule_name_formatter(name),
        Targets=[
            {
                'Id': rule_name_formatter(name),
                'Arn': os.environ.get('SEND_FUNCTION_ARN'),
                'Input': json.dumps(input_object),
            }
        ]
    )
    LOG.debug(response)

def delete_cloudwatch_target(name):
    response = CLOUDWATCH_EVENTS_CLIENT.remove_targets(
        Rule=rule_name_formatter(name),
        Ids=[rule_name_formatter(name)]
    )
    LOG.debug(response)

def delete_cloudwatch_rule(name):
    response = CLOUDWATCH_EVENTS_CLIENT.delete_rule(
        Name=rule_name_formatter(name)
    )
    LOG.debug(response)