import io

import pytest
import boto3
import moto
from PIL import Image

from flask_bloggy import db


@pytest.fixture
def database(table):
    return db.Database(table)


@pytest.fixture
def table_name():
    return 'TestBloggy'


@pytest.fixture
def images_bucket_name():
    return 'bloggy-images'


@pytest.fixture
def s3_client():
    with moto.mock_aws():
        yield boto3.client('s3')


@pytest.fixture
def post_image(s3_client, images_bucket_name, images_bucket):
    name = 'test.jpg'
    buffer = io.BytesIO()
    image = Image.new('RGB', (100, 100))
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    s3_client.upload_fileobj(buffer, images_bucket_name, name)
    yield name


@pytest.fixture
def images_bucket(s3_client, images_bucket_name):
    yield s3_client.create_bucket(Bucket=images_bucket_name)


@pytest.fixture(autouse=True)
def aws_creds(monkeypatch, table_name, images_bucket_name):
    # Make sure that no tests try to use real AWS creds
    monkeypatch.setenv('BLOGGY_TABLE_NAME', table_name)
    monkeypatch.setenv('BLOGGY_IMAGES_BUCKET_NAME', images_bucket_name)
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')


@pytest.fixture
def dynamodb():
    with moto.mock_aws():
        yield boto3.client('dynamodb')


@pytest.fixture
def table(table_name):
    with moto.mock_aws():
        dynamodb = boto3.resource('dynamodb')
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'pk',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'sk',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'pk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'sk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'gsi1pk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'gsi1sk',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'gsi1',
                    'KeySchema': [
                        {
                            'AttributeName': 'gsi1pk',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'gsi1sk',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                }
            ]
        )
        yield table_name
