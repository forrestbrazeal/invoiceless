# invoiceless

Invoiceless is a serverless API for sending simple recurring invoices by email using AWS Lambda, API Gateway, CloudWatch Events, and SES.

## Quick Deploy

[<img src="./img/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=us-east-1/stacks/new?stackName=invoiceless&templateURL=https://s3.amazonaws.com/rboyd-sarbucket/packaged.yaml) 



## Deployment Instructions

0. Make sure you have the AWS CLI installed
1. Clone the repository
2. From the top level directory, run

`aws cloudformation package --template-file template.yaml --s3-bucket [your s3 bucket] --output-template-file packaged.yaml`

`aws cloudformation deploy --template-file ./packaged.yaml --stack-name invoiceless --capabilities CAPABILITY_IAM`

## Using the API

### POST /invoices
Sends an invoice immediately to the recipients specified in `agreement_info.client_emails`.

#### Notes

`agreement_info.verified_sender_arn` is optional and only needs to be specified if your AWS SES account is still on probation. You can verify the address in `agreement_info.provider_email` by following the steps from AWS [here](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/verify-email-addresses.html).

`agreement_info.net` specifies the number of days until the invoice is due. It can be any integer from 1 to 120.

#### Example call

```
headers = {'content-type': 'application/json'}
url = '[api URL]/invoices/'

body = {
  "agreement_info": {
    "net": 30,
    "client_emails": [
      "accounts_payable@company.com",
      "
    ],
    "provider_email": "me@mybusiness.com",
    "verified_sender_arn": "arn:aws:ses:us-east-1:[account]:identity/me@mybusiness.com"
  },
  "client_info": {
    "client_id": "1001",
    "name": "My Client",
    "street": "1 Corporate Pkwy",
    "city": "Bigcity",
    "state": "TX",
    "country": "USA",
    "post_code": "01010"
  },
  "service_provider_info": {
    "name": "My Name",
    "street": "123 Main St",
    "city": "Anywhere",
    "state": "NY",
    "country": "USA",
    "post_code": "12345"
  },
  "line_items": [
    {
      "name": "Widgets",
      "description": "Default widgets",
      "units": 10,
      "unit_price": 125
    },
    {
      "name": "Customized Widgets",
      "description": "Reinforced widgets",
      "units": 10,
      "unit_price": 125
    }
  ]
}

requests.post(url, data=json.dumps(body), headers=headers)


```

### POST invoices/schedule

This call creates a CloudWatch rule that sends your invoice on a recurring schedule that you specify.

The API request looks the same as the example above, except for the addition of a top-level body attribute called `schedule_expression`:

```
body = {
  "schedule_expression": "cron(0 12 25 * ? *)",
  "agreement_info": {
    ...
```

Refer to AWS's [schedule expressions syntax guide](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html) for help creating your schedule.

The example above will send a recurring invoice on the 25th day of every month at 12:00 PM.

### DELETE invoices/schedule/client_id

Removes the CloudWatch Events rule for the specified client ID. Note that Invoiceless only supports one recurring invoice per client at the moment.

## Generated Invoices

Invoiceless uses PyInvoice to generate simple invoices that will be sent via email to the destination addresses you specify.

![Example Invoice](example_email.png?raw=true)
