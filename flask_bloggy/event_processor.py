from opentelemetry import trace

from . import models, tracing

tracer = trace.get_tracer(__name__)


def _create_post_from_event_detail(event_detail, database):
    tags = database.get_tags_by_names(event_detail.tags)

    post = models.Post(
        title=event_detail.title,
        body=event_detail.body,
        tags=tags,
        main_image=event_detail.main_image,
        slug=event_detail.slug,
        created=event_detail.created
    )
    return post


def _process_post_created(event, database):
    if not event.post.published:
        return
    post = _create_post_from_event_detail(event.post, database)
    database.save_published_post(post)


def _process_post_updated(event, database):
    if event.old.published and not event.new.published:
        database.delete_published_post(event.old.slug)
    elif not event.old.published and event.new.published:
        post = _create_post_from_event_detail(event.new, database)
        database.save_published_post(post)
    elif event.old.published and event.new.published:
        tags_removed = event.old.tags.difference(event.new.tags)
        post = _create_post_from_event_detail(event.new, database)
        database.update_published_post(post, tags_removed)


def _process_post_deleted(event, database):
    if event.old.published:
        database.delete_published_post(event.old.slug)


def _process_tag_created(event, database):
    database.save_tag(models.Tag(
        name=event.tag.name,
        label=event.tag.label
    ))


def _process_tag_updated(event, database):
    database.update_tag_label(models.Tag(
        name=event.new.name,
        label=event.new.label
    ))


def _process_tag_deleted(event, database):
    database.delete_tag(event.tag.name)


@tracer.start_as_current_span("process_event")
def _process_event(event, database):
    tracing.set_attr('event_type', event.event_type)
    if event.event_type == 'post_created':
        tracing.set_attr('slug', event.post.slug)
        _process_post_created(event, database)
    elif event.event_type == 'post_updated':
        tracing.set_attr('slug', event.new.slug)
        _process_post_updated(event, database)
    elif event.event_type == 'post_deleted':
        tracing.set_attr('slug', event.old.slug)
        _process_post_deleted(event, database)
    elif event.event_type == 'tag_created':
        tracing.set_attr('tag', event.tag.name)
        _process_tag_created(event, database)
    elif event.event_type == 'tag_updated':
        tracing.set_attr('tag', event.new.name)
        _process_tag_updated(event, database)
    elif event.event_type == 'tag_deleted':
        tracing.set_attr('tag', event.old.name)
        _process_tag_deleted(event, database)


@tracer.start_as_current_span("process")
def process(events, database):
    for event in events:
        _process_event(event, database)
