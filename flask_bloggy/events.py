"""
This module contains the events that are emitted by the bloggy-admin
application.
"""
import dataclasses
import datetime


@dataclasses.dataclass
class Tag:
    name: str
    label: str
    version: int = 1


@dataclasses.dataclass
class Image:
    filename: str
    desc: str
    title: str
    url: str


@dataclasses.dataclass
class Post:
    slug: str
    title: str
    body: str
    published: bool
    main_image: Image
    tags: set[str] = dataclasses.field(default_factory=set)
    created: datetime.datetime = datetime.datetime.now()
    version: int = 1

    def copy(self, **kwargs):
        return dataclasses.replace(self, **kwargs)


@dataclasses.dataclass
class PostCreatedEvent:
    post: Post
    event_type: str = 'post_created'


@dataclasses.dataclass
class PostDeletedEvent:
    old: Post
    event_type: str = 'post_deleted'


@dataclasses.dataclass
class PostUpdatedEvent:
    old: Post
    new: Post
    event_type: str = 'post_updated'


@dataclasses.dataclass
class TagCreatedEvent:
    tag: Tag
    event_type: str = 'tag_created'


@dataclasses.dataclass
class TagDeletedEvent:
    old: Tag
    event_type: str = 'tag_deleted'


@dataclasses.dataclass
class TagUpdatedEvent:
    old: Tag
    new: Tag
    event_type: str = 'tag_updated'
