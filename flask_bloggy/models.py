"""
This module contains the model classes for the bloggy site application.

The models in this module are similar to that in the events module, but
are slightly different, optimised for the site use case.
"""
import dataclasses
import datetime


@dataclasses.dataclass(frozen=True)
class Tag:
    name: str
    label: str

    def copy(self, **kwargs):
        return dataclasses.replace(self, **kwargs)


@dataclasses.dataclass(frozen=True)
class Image:
    location: str
    desc: str
    title: str

    def copy(self, **kwargs):
        return dataclasses.replace(self, **kwargs)


@dataclasses.dataclass(frozen=True)
class Post:
    slug: str
    title: str
    body: str
    main_image: Image
    tags: set[Tag] = dataclasses.field(default_factory=set)
    created: datetime.datetime = datetime.datetime.now()

    def update_tag(self, tag):
        for t in self.tags:
            if t.name == tag.name:
                self.tags.remove(t)
                self.tags.add(tag)
                return

    def copy(self, **kwargs):
        return dataclasses.replace(self, **kwargs)
