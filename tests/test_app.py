from datetime import datetime
import re

import pytest

from flask_bloggy import create_app, event_processor, events

from . import factories
from .utils import days_ago


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return app.test_client()


def tag(name, label):
    return events.Tag(name=name, label=label)


@pytest.fixture
def tags(database):
    event_processor.process(
        [
            events.TagCreatedEvent(tag=tag('test_tag', '!Test Tag!')),
            events.TagCreatedEvent(tag=tag('tag_x', '!Tag X!')),
            events.TagCreatedEvent(tag=tag('tag_y', '!Tag Y!'))
        ],
        database
    )


@pytest.fixture
def posts(database, tags):
    event_processor.process(
        [
            events.PostCreatedEvent(
                post=post(1, True, days_ago(12), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(2, True, days_ago(11), {'test_tag', 'tag_x'})
            ),
            events.PostCreatedEvent(
                post=post(3, True, days_ago(10), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(4, True, days_ago(9), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(5, True, days_ago(8), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(6, True, days_ago(7), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(7, False, days_ago(6), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(8, True, days_ago(5), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(9, True, days_ago(4), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(10, True, days_ago(3), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(11, True, days_ago(2), {'test_tag'})
            ),
            events.PostCreatedEvent(
                post=post(12, True, days_ago(1), {'test_tag'})
            )
        ],
        database
    )


def post(n, published, created=datetime.now(), tags={}):
    return factories.EventPostFactory(
        slug=f'post{n}',
        title=f'!Post {n}!',
        published=published,
        created=created,
        tags=tags
    )


def test_list_posts(client, posts):
    response = client.get("/posts/")
    assert response.status_code == 200
    assert b"!Post 1!" not in response.data  # paging
    assert b"!Post 7!" not in response.data  # not published
    assert b"!Post 2!" in response.data
    assert b"!Post 11!" in response.data
    assert b"!Post 12!" in response.data

    # now pull out the paging link and try the next page
    def get_paging_link(page):
        return re.findall(
            rf'href="(/posts/\?pt=[a-zA-Z0-9]+\&page={page})"',
            response.data.decode('utf-8')
        )[0]
    link = get_paging_link(2)

    response = client.get(link)
    assert response.status_code == 200
    assert b'!Post 2!' not in response.data
    assert b'!Post 1!' in response.data

    link = get_paging_link(1)

    # and now go back
    response = client.get(link)
    assert response.status_code == 200
    assert b'!Post 2!' in response.data
    assert b'!Post 1!' not in response.data


def test_view_post(client, posts):
    response = client.get("/posts/post1/")
    assert response.status_code == 200
    assert b"!Post 1!" in response.data


def test_view_unpublished_post(client, posts):
    response = client.get("/posts/post7/")
    assert response.status_code == 404


def test_view_non_existent_post(client, posts):
    response = client.get("/posts/post999/")
    assert response.status_code == 404


@pytest.mark.parametrize("tag", ["", "asdf!", "asdf}"])
def test_list_tags_with_invalid_tag(client, tag):
    response = client.get(f"/posts/?tag={tag}")
    assert response.status_code == 400


def test_list_posts_by_tag(client, posts):
    response = client.get("/posts/?tag=test_tag")
    assert response.status_code == 200
    assert b"!Post 1!" not in response.data  # paging
    assert b"!Post 7!" not in response.data  # not published
    assert b"!Post 2!" in response.data
    assert b"!Post 11!" in response.data
    assert b"!Post 12!" in response.data

    # now pull out the paging link and try the next page
    def get_paging_link(page):
        return re.findall(
            rf'href="(/posts/\?tag=test_tag&pt=[a-zA-Z0-9]+\&page={page})"',
            response.data.decode('utf-8')
        )[0]
    link = get_paging_link(2)

    response = client.get(link)
    assert response.status_code == 200
    assert b'!Post 2!' not in response.data
    assert b'!Post 1!' in response.data

    link = get_paging_link(1)

    # and now go back
    response = client.get(link)
    assert response.status_code == 200
    assert b'!Post 2!' in response.data
    assert b'!Post 1!' not in response.data

    # now try a tag that doesn't exist
    response = client.get("/posts/?tag=not_a_tag")
    assert response.status_code == 200
    for i in range(1, 12+1):
        assert f'!Post {i}!'.encode() not in response.data


def test_update_tag_label(client, posts, database):

    # what if we update a tag label?
    response = client.get("/posts/?tag=tag_x")
    assert response.status_code == 200
    assert b'!Post 2!' in response.data
    assert b'!Post 12!' not in response.data
    assert b'!Tag X!' in response.data

    event_processor.process([events.TagUpdatedEvent(
        new=tag('tag_x', '!Tag X Updated!'),
        old=tag('tag_x', '!Tag X!')
    )], database)
    response = client.get("/posts/?tag=tag_x")
    assert response.status_code == 200
    assert b'!Post 2!' in response.data
    assert b'!Post 12!' not in response.data
    assert b'!Tag X!' not in response.data
    assert b'!Tag X Updated!' in response.data


def test_show_image_does_not_exist(client, post_image):
    response = client.get("/posts/images/does_not_exist.jpg")
    assert response.status_code == 404


def test_show_image(client, post_image):
    response = client.get(f'/posts/images/{post_image}')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'image/jpeg'
    assert response.data.startswith(b'\xff\xd8')  # jpeg header
