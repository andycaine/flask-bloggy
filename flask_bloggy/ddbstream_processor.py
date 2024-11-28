import datetime
import os

from opentelemetry import trace

from .events import (
    PostCreatedEvent, PostUpdatedEvent, PostDeletedEvent, Post, Image
)
from .event_processor import process
from .db import Database
from .util import dynamodb_to_dict


def make_handler():
    def inner(event, _):
        table_name = os.environ.get('BLOGGY_TABLE_NAME')
        database = Database(table_name)
        handler(event, database)

    return inner


def item_to_post(item):
    return Post(
        slug=item['slug'],
        title=item['title'],
        body=item['body'],
        published=item['published'],
        tags='tags' in item and item['tags'] or set(),
        main_image=Image(
            filename=item['main_image']['filename'],
            desc=item['main_image']['desc'],
            url=item['main_image']['url'],
            title=item['main_image']['title']
        ),
        created=datetime.datetime.fromisoformat(item['created']),
        version=item['version']
    )


def handler(event, database):
    span = trace.get_current_span()
    span.set_attribute('ddbstream_processor.event', event)
    span.set_attribute('ddbstream_processor.record_count',
                       len(event['Records']))

    events = []

    for rec in event['Records']:
        detail = rec['dynamodb']
        new = dynamodb_to_dict(detail.get('NewImage', {}))
        old = dynamodb_to_dict(detail.get('OldImage', {}))

        item_type = new and _type(new) or _type(old)
        if item_type != 'Post':
            span.add_event(
                'invalid_type',
                {'type': item_type, 'detail': detail}
            )
            continue

        event_name = rec['eventName']
        if event_name == 'INSERT':
            events.append(PostCreatedEvent(item_to_post(new)))
        elif event_name == 'MODIFY':
            events.append(PostUpdatedEvent(item_to_post(old),
                                           item_to_post(new)))
        elif event_name == 'REMOVE':
            events.append(PostDeletedEvent(item_to_post(old)))

    process(events, database)


def _type(item):
    return item.get('type')
