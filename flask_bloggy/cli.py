import datetime

import click
import flask_bloggy
from flask_bloggy.models import Post, Image, Tag
from flask_bloggy.db import Database
import nsst
import boto3


@click.command()
def run():
    flask_bloggy.run()


def _connect(table_name):
    return nsst.Table(table_name)


@click.command()
@click.option('--table-name', prompt=True, required=True)
def create_table(table_name):
    _connect(table_name).create_table()


@click.command()
@click.option('--bucket-name', prompt=True, required=True)
def create_bucket(bucket_name):
    boto3.client('s3').create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
            'LocationConstraint': 'eu-west-2'
        }
    )


@click.command()
@click.option('--table-name', prompt=True, required=True)
def delete_table(table_name):
    dynamodb = boto3.resource('dynamodb')
    dynamodb.Table(table_name.table_name).delete()


@click.command()
@click.option('--bucket-name', prompt=True, required=True)
def delete_bucket(bucket_name):
    bucket = boto3.resource('s3').Bucket(bucket_name)
    bucket.objects.all().delete()

    boto3.client('s3').delete_bucket(Bucket=bucket_name)


def upload_to_s3(bytes, bucket_name, key):
    s3 = boto3.client('s3')
    s3.put_object(
        Body=bytes,
        Bucket=bucket_name,
        Key=key,
        ContentType='image/jpeg'
    )


@click.command()
@click.option('--table-name', prompt=True, required=True)
@click.option('--bucket-name', prompt=True, required=True)
def generate_posts(table_name, bucket_name):
    try:
        import faker
        fake = faker.Faker()
        db = Database(table_name)
        for i in range(1, 15):
            img_data = fake.image(image_format='jpeg')
            img_name = fake.file_name(category='image', extension='jpg')
            upload_to_s3(img_data, bucket_name, f'post-{i}/{img_name}')
            post = Post(
                slug=f'post-{i}',
                title=f'Post {i}',
                body=fake.paragraphs(nb=30),
                main_image=Image(
                    desc=fake.sentence(nb_words=5),
                    title=fake.sentence(nb_words=5),
                    location=f'post-{i}/{img_name}'
                ),
                tags={
                    Tag(name='tag1', label='Tag 1'),
                    Tag(name='tag2', label='Tag 2')
                },
                created=datetime.datetime.now()
            )
            db.save_published_post(post)

    except ImportError:
        raise click.UsageError('Please install faker: pip install faker')


@click.group()
def cli():
    pass


cli.add_command(run)
cli.add_command(create_bucket)
cli.add_command(create_table)
cli.add_command(delete_bucket)
cli.add_command(delete_table)
cli.add_command(generate_posts)

if __name__ == '__main__':
    cli()
