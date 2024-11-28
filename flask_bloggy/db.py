import datetime

from opentelemetry import trace

from . import models
import nsst
from .tracing import set_attr


tracer = trace.get_tracer(__name__)


def _ignore():
    pass


def post_pk(slug):
    return f'bloggy_post#{slug}'


def post_sk(slug, tag_name='#'):
    return f'bloggy_post#{slug}#tag#{tag_name}'


def post_gsi1pk(tag_name='#'):
    return f'bloggy_post#tag#{tag_name}'


def post_key(slug, tag_name='#'):
    return dict(pk=post_pk(slug), sk=post_sk(slug, tag_name))


def tag_pk(name):
    return f'bloggy_tag#{name}'


tag_sk = tag_pk


def post_to_item(post, tag_name='#'):
    created = post.created.isoformat()
    item = dict(
        pk=post_pk(post.slug),
        sk=post_sk(post.slug, tag_name),
        gsi1pk=post_gsi1pk(tag_name),
        gsi1sk=created,
        slug=post.slug,
        title=post.title,
        body=post.body,
        main_image=dict(
            location=post.main_image.location,
            desc=post.main_image.desc,
            title=post.main_image.title
        ),
        created=created,
        type='#' and 'BloggyPost' or 'BloggyPostTagMapping'
    )
    # dynamodb doesn't support empty sets
    if post.tags:
        item['tags'] = [
            dict(name=t.name, label=t.label)
            for t in post.tags
        ]
    return item


def tag_to_item(tag):
    return dict(
        pk=tag_pk(tag.name),
        sk=tag_sk(tag.name),
        gsi1pk='bloggy_tag#',
        gsi1sk=tag.name,
        name=tag.name,
        label=tag.label,
        type='BloggyTag'
    )


def tags_from_items(items):
    return set(map(lambda item: item_to_tag(item), items))


def item_to_post(item):
    return models.Post(
        slug=item['slug'],
        title=item['title'],
        body=item['body'],
        tags=tags_from_items(item.get('tags', {})),
        main_image=models.Image(
            location=item['main_image']['location'],
            desc=item['main_image']['desc'],
            title=item['main_image']['title']
        ),
        created=datetime.datetime.fromisoformat(item['created'])
    )


def item_to_tag(item):
    return models.Tag(
        name=item['name'],
        label=item['label']
    )


def create_esk(paging_key, tag):
    if paging_key is None:
        return None

    slug = paging_key["slug"]
    return dict(pk=post_pk(slug),
                sk=post_sk(slug, tag),
                gsi1pk=post_gsi1pk(tag),
                gsi1sk=f'{paging_key["created"]}')


def create_paging_key(last_evaluated_key):
    if last_evaluated_key is None:
        return None
    return dict(
        slug=last_evaluated_key['sk'].split('#')[1],
        created=last_evaluated_key['gsi1sk']
    )


class Database:

    def __init__(self, table_name):
        self.table = nsst.Table(table_name)
        self.published = {}

    @tracer.start_as_current_span('Database.get_published_posts')
    def get_published_posts(self, tag=None, limit=10, paging_key=None):
        tag = tag or '#'
        esk = create_esk(paging_key, tag)
        posts, lek = self.table.query_gsi1(
            post_gsi1pk(tag), transformer=item_to_post, limit=limit,
            esk=esk, auto_page=False, reverse=True
        )

        set_attr('flask_bloggy.last_evaluated_key', str(lek))

        next_paging_key = create_paging_key(lek)
        set_attr('flask_bloggy.next_paging_key', str(next_paging_key))

        return posts, next_paging_key

    @tracer.start_as_current_span('Database.get_published_post')
    def get_published_post(self, slug, on_not_found=_ignore()):
        set_attr('flask_bloggy.slug', slug)
        return self.table.get_item(
            pk=post_pk(slug),
            sk=post_sk(slug),
            transformer=item_to_post,
            on_not_found=on_not_found
        )

    def get_tags(self, limit=100, esk=None):
        yield from self.table.query_gsi1(
            'bloggy_tag#',
            transformer=item_to_tag,
            limit=limit,
            esk=esk
        )

    def get_tags_by_names(self, names):
        if not names:
            return set()
        keys = [dict(pk=tag_pk(name), sk=tag_sk(name))
                for name in names]
        return self.table.get_items(keys=keys, transformer=item_to_tag)

    def save_tag(self, tag):
        self.table.put_item(**tag_to_item(tag))

    def save_published_post(self, post):
        items = []

        # this is the main item representing the post
        items.append(post_to_item(post))

        # now create an item for each tag to query by tag
        for tag in post.tags:
            items.append(post_to_item(post, tag_name=tag.name))
        self.table.batch_write(puts=items)

    def delete_published_post(self, post):
        keys_to_delete = [post_key(post.slug)]
        for tag in post.tags:
            keys_to_delete.append(post_key(post.slug, tag.name))
        self.table.delete_items(keys_to_delete)

    def update_published_post(self, post, tags_removed):
        keys_to_delete = [post_key(post.slug)]
        for tag in tags_removed:
            keys_to_delete.append(post_key(post.slug, tag.name))
        self.table.delete_items(keys_to_delete)
        self.save_published_post(post)

    def update_tag_label(self, tag):
        self.table.put_item(**tag_to_item(tag))

        posts, _ = self.get_published_posts(tag=tag.name)
        for post in posts:
            post.update_tag(tag)
            self.save_published_post(post)
