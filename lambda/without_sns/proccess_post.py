import boto3
import botocore
import hashlib

aws_region="us-west-2"
dynamodb = boto3.resource('dynamodb')
dynamodb_table = "txt2mp3"
bucket_name = "mp3polly"
polly_client = boto3.client('polly')


def put_item_in_table(tablename, text, s3_url):
    txt = text.encode('utf-8')
    uuid = hashlib.sha256(txt).hexdigest()
    table = dynamodb.Table(tablename)
    table.put_item(
        Item={
            'uuid': uuid,
            'text': text,
            's3_url': s3_url
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


def synthesize_speech(text):
    txt = text.encode('utf-8')
    uuid = hashlib.sha256(txt).hexdigest()
    audio_filename = uuid + '.mp3'
    response = polly_client.synthesize_speech(OutputFormat='mp3',
        Text=text,
        VoiceId='Russell')
    audios_stream = response['AudioStream'].read()
    audio_file = open('/tmp/' + audio_filename, 'wb')
    audio_file.write(audios_stream)
    audio_file.close()
    return audio_filename


def check_s3_file_exists(bucketname, filename):
    s3 = boto3.resource('s3')
    try:
        s3.Object(bucketname, filename).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            exists = False
        else:
            raise
    else:
        exists = True
    return exists


def upload_to_s3(bucketname, filename):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketname)
    bucket.upload_file('/tmp/' + filename, filename)
    while not check_s3_file_exists(bucketname, filename):
        print("Waiting for file to finish uploading")
    s3_url = "https://s3-" + aws_region + ".amazonaws.com/" + bucket_name + "/" + filename
    return s3_url


def lambda_handler(event, context):
    text = event['text']
    result = get_item_by_name(dynamodb_table, text)
    if result == "":
        audio_filename = synthesize_speech(text)
        s3_url = upload_to_s3(bucket_name, audio_filename)
        uuid = put_item_in_table(dynamodb_table, text, s3_url)
        return {
            'message': "Item successfully saved to database",
            'uuid': uuid,
            'url': s3_url
        }
    else:
        return {
            'message': "This text item already exists in database",
            'text': result['text'],
            'uuid': result['uuid'],
            'url': result['s3_url']
        }


if __name__ == "__main__":
    # event = {'text': "What is your name?"}
    result = lambda_handler("I am cool software developer", "context")
    print(result.get('message', 'Unknown field message'))
    print(result.get('url', 'Unknown field url'))
