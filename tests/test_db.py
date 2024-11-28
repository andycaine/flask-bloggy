import pytest

from flask_bloggy import models

from . import factories
from .utils import days_ago


@pytest.fixture
def tags(database):
    tags = []
    for i in range(1, 4):
        tag = factories.TagFactory(name=f'tag{i}', label=f'Tag {i}')
        database.save_tag(tag)
        tags.append(tag)
    yield tags


@pytest.fixture
def post1(database, tags):
    post = factories.PostFactory(slug='post1', tags={tags[0], tags[1]},
                                 created=days_ago(3))
    database.save_published_post(post)
    yield post


@pytest.fixture
def post2(database, tags):
    post = factories.PostFactory(slug='post2', tags={tags[1], tags[2]},
                                 created=days_ago(2))
    database.save_published_post(post)
    yield post


@pytest.fixture
def post3(database):
    post = factories.PostFactory(slug='post3', tags=set(),
                                 created=days_ago(1))
    database.save_published_post(post)
    yield post


@pytest.fixture
def get_posts(database):
    def _get_posts(**kwargs):
        posts, _ = database.get_published_posts(**kwargs)
        return posts
    return _get_posts


def get_tag(name, tags):
    return next((t for t in tags if t.name == name), None)


def test_get_published_posts(database, post1, post2, post3):
    posts, lek = database.get_published_posts()
    assert lek is None
    assert posts == [post3, post2, post1]

    posts, lek = database.get_published_posts(limit=2)
    assert lek is not None
    assert posts == [post3, post2]

    posts, lek = database.get_published_posts(limit=2, paging_key=lek)
    assert lek is None
    assert posts == [post1]


def test_get_published_posts_by_tag(database, post1, post2, post3):
    posts, lek = database.get_published_posts(tag='tag2')
    assert lek is None
    assert posts == [post2, post1]

    posts, lek = database.get_published_posts(limit=1, tag='tag2')
    assert lek is not None
    assert posts == [post2]

    posts, lek = database.get_published_posts(limit=1, paging_key=lek)
    assert lek is None
    assert posts == [post1]


def test_get_published_post(database, post2):
    post = database.get_published_post(post2.slug)
    assert post == post2


def test_get_tags(database, tags):
    assert list(database.get_tags()) == [
        models.Tag(name='tag1', label='Tag 1'),
        models.Tag(name='tag2', label='Tag 2'),
        models.Tag(name='tag3', label='Tag 3'),
    ]


def test_get_tags_by_names(database, tags):
    result = list(database.get_tags_by_names(['tag1', 'tag2']))
    assert result == [
        models.Tag(name='tag1', label='Tag 1'),
        models.Tag(name='tag2', label='Tag 2'),
    ]


def test_update_tag_label_updates_posts(database, post1, post2):

    def tag_label(post, tag_name):
        return next((t.label for t in post.tags if t.name == tag_name), None)

    assert tag_label(post1, 'tag2') == 'Tag 2'
    assert tag_label(post2, 'tag2') == 'Tag 2'

    database.update_tag_label(models.Tag(name='tag2', label='Tag 2 Updated'))

    post1 = database.get_published_post(post1.slug)
    assert tag_label(post1, 'tag2') == 'Tag 2 Updated'

    post2 = database.get_published_post(post2.slug)
    assert tag_label(post2, 'tag2') == 'Tag 2 Updated'


def test_delete_published_post(database, post1, post2, post3):
    database.delete_published_post(post1)

    posts, _ = database.get_published_posts()
    assert posts == [post3, post2]

    posts, _ = database.get_published_posts(tag='tag2')
    assert posts == [post2]


def test_update_post_title(database, post1, get_posts):
    update_title = 'Updated Title'
    database.save_published_post(post1.copy(title=update_title))
    assert database.get_published_post('post1').title == update_title
    assert next(iter(get_posts())).title == update_title
    assert next(iter(get_posts(tag='tag1'))).title == update_title
    assert next(iter(get_posts(tag='tag2'))).title == update_title
    assert len(get_posts(tag='tag3')) == 0


def test_update_post_change_tags(database, post1, tags, get_posts):
    tag1 = get_tag('tag1', tags)
    tag2 = get_tag('tag2', tags)
    tag3 = get_tag('tag3', tags)
    post = post1.copy(tags={tag1, tag3})  # add tag3, remove tag2
    database.update_published_post(post, [tag2])

    assert next(iter(get_posts(tag='tag1'))).slug == 'post1'
    assert len(get_posts(tag='tag2')) == 0
    assert next(iter(get_posts(tag='tag3'))).slug == 'post1'
