from unittest.mock import Mock

import pytest

from flask_bloggy import event_processor, events, models
from . import factories


def stub_get_tags_by_names(tags):
    result = set()
    for t in tags:
        if t == 'tag1':
            result.add(models.Tag(name='tag1', label='Tag 1'))
        elif t == 'tag2':
            result.add(models.Tag(name='tag2', label='Tag 2'))
    return result


@pytest.fixture
def database():
    mock = Mock()
    mock.get_tags_by_names = stub_get_tags_by_names
    yield mock


def test_unpublished_post_created(database):
    event_processor.process([
        events.PostCreatedEvent(
            post=factories.EventPostFactory.create(slug='post1',
                                                   published=False)
        )
    ], database)
    database.save_published_post.assert_not_called()


def test_published_post_created(database):
    evt_detail = factories.EventPostFactory.create(
        slug='post1',
        tags=['tag1', 'tag2'],
        published=True
    )

    event_processor.process([
        events.PostCreatedEvent(
            post=evt_detail
        )
    ], database)
    database.save_published_post.assert_called_once_with(
        models.Post(
            title=evt_detail.title,
            slug=evt_detail.slug,
            body=evt_detail.body,
            main_image=evt_detail.main_image,
            tags=stub_get_tags_by_names(evt_detail.tags),
            created=evt_detail.created
        )
    )


def test_published_post_unpublished(database):
    old = factories.EventPostFactory.create(
        slug='post1',
        published=True
    )
    new = old.copy(published=False)

    event_processor.process([
        events.PostUpdatedEvent(
            old=old,
            new=new
        )
    ], database)
    database.delete_published_post.assert_called_once_with('post1')


def test_unpublished_post_published_and_updated(database):
    old = factories.EventPostFactory.create(
        slug='post1',
        published=False
    )
    new = old.copy(published=True, title='New title')

    event_processor.process([
        events.PostUpdatedEvent(
            old=old,
            new=new
        )
    ], database)
    database.save_published_post.assert_called_once_with(
        models.Post(
            title='New title',
            slug=new.slug,
            body=new.body,
            main_image=new.main_image,
            tags=stub_get_tags_by_names(new.tags),
            created=new.created
        )
    )


def test_published_post_updated(database):
    old = factories.EventPostFactory.create(
        slug='post1',
        published=True
    )
    new = old.copy(title='New title')

    event_processor.process([
        events.PostUpdatedEvent(
            old=old,
            new=new
        )
    ], database)
    database.update_published_post.assert_called_once_with(
        models.Post(
            title='New title',
            slug=new.slug,
            body=new.body,
            main_image=new.main_image,
            tags=stub_get_tags_by_names(new.tags),
            created=new.created
        ), set()
    )


def test_published_post_tags_removed(database):
    old = factories.EventPostFactory.create(
        slug='post1',
        published=True,
        tags={'tag1', 'tag2'}
    )
    new = old.copy(tags={'tag1'})

    event_processor.process([
        events.PostUpdatedEvent(
            old=old,
            new=new
        )
    ], database)
    database.update_published_post.assert_called_once_with(
        models.Post(
            title=new.title,
            slug=new.slug,
            body=new.body,
            main_image=new.main_image,
            tags=stub_get_tags_by_names(new.tags),
            created=new.created
        ), {'tag2'}
    )


def test_published_post_tags_added(database):
    old = factories.EventPostFactory.create(
        slug='post1',
        published=True,
        tags={'tag1'}
    )
    new = old.copy(tags={'tag1', 'tag2'})

    event_processor.process([
        events.PostUpdatedEvent(
            old=old,
            new=new
        )
    ], database)
    database.update_published_post.assert_called_once_with(
        models.Post(
            title=new.title,
            slug=new.slug,
            body=new.body,
            main_image=new.main_image,
            tags=stub_get_tags_by_names(new.tags),
            created=new.created
        ), set()
    )
