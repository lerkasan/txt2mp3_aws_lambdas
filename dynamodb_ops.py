import boto3
import uuid
import hashlib

dynamodb = boto3.resource('dynamodb')


def create_txt2mp3_table(tablename):
    table = dynamodb.create_table(
        TableName=tablename,
        KeySchema=[
            {
                'AttributeName': 'uuid',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'uuid',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    table.meta.client.get_waiter('table_exists').wait(TableName=tablename)


def put_item_in_table(tablename, text, s3_url):
    table = dynamodb.Table(tablename)
    table.put_item(
        Item={
            #'uuid': hashlib.sha256(text).hexdigest(),
            'uuid': str(uuid.uuid4()),
            'text': text,
            's3_url': s3_url,
        }
    )


def lambda_handler(event, context):
    put_item_in_table("txt2mp3",  event['text'], "my_s3_bucket_file_url")


def hash_me(text):
    result = hashlib.sha256(text).hexdigest()
    print(result)


if __name__ == "__main__":
    create_txt2mp3_table("txt2mp3")
   # put_item_in_table("txt2mp3", "lerkasan", "my_s3_bucket_file_url")
   # hash_me("Hello world2")

