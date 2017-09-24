import boto3
import hashlib

aws_region = "us-west-2"
dynamodb = boto3.resource('dynamodb')
dynamodb_table = "txt2mp3"


def get_item_by_name(table_name, text):
    txt = text.encode('utf-8')
    table = dynamodb.Table(table_name)
    value = table.get_item(
        TableName=table_name,
        Key={
            'uuid': hashlib.sha256(txt).hexdigest()
        }
    )
    if 'Item' not in value:
        return ""
    return value['Item']


def lambda_handler(event, context):
    if 'text' in event:
        text = event['text']
        result = get_item_by_name(dynamodb_table, text)
        if result == "":
            return {
                'message': "Given text item is absent in the database",
                'text': text
            }
        else:
            return {
                'message': "This text item exists in database",
                'text': result['text'],
                'uuid': result['uuid'],
                'url': result['s3_url']
            }
    if 'uuid' in event['pathParameters']:
        uuid = event['uuid']
        table = dynamodb.Table(dynamodb_table)
        result = table.get_item(
            TableName=dynamodb_table,
            Key={'uuid': uuid}
        )
        if 'Item' not in result:
            return {
                'message': "Given uuid is absent in the database",
                'uuid': uuid
            }
        else:
            return {
                'message': "This uuid item exists in database",
                'text': result['text'],
                'uuid': result['uuid'],
                'url': result['s3_url']
            }
