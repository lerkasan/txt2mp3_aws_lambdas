import boto3
import botocore
import hashlib

aws_region="us-west-2"
dynamodb = boto3.resource('dynamodb')
dynamodb_table = "txt2mp3"


def put_item_in_table(tablename, text):
    txt = text.encode('utf-8')
    uuid = hashlib.sha256(txt).hexdigest()
    table = dynamodb.Table(tablename)
    table.put_item(
        Item={
            'uuid': uuid,
            'text': text
        }
    )
    while not get_item_by_uuid(table, uuid):
        print("Waiting for item to be saved to DynamoDB")
    return uuid


def get_item_by_uuid(table, uuid):
    response = table.get_item(
        Key={
            'uuid': uuid
        }
    )
    return response['Item']


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
    text = event['text']
    result = get_item_by_name(dynamodb_table, text)
    if result == "":
        uuid = put_item_in_table(dynamodb_table, text)
        # Send notification about new post to SNS
        sns_client = boto3.client('sns')
        sns_topic_arn = "arn:aws:sns:us-west-2:370535134506:text2audio"
        sns_client.publish(TopicArn = sns_topic_arn, Message = uuid)
        return {
            'message': "Item converting is pending",
            'uuid': uuid
        }
    else:
        return {
            'message': "This text item already exists in database",
            'text': result['text'],
            'uuid': result['uuid']
        }