import re

from flask import (
    render_template, abort, current_app, Blueprint, request, make_response
)
from markupsafe import escape
from opentelemetry import trace
from web_paging import flask_pageable

tracer = trace.get_tracer(__name__)


def _404():
    return abort(404)


blueprint = Blueprint('bloggy', __name__, template_folder='templates')


def get_db():
    return current_app.extensions['bloggy'].db


@tracer.start_as_current_span('list_posts')
@blueprint.get('/')
@flask_pageable('bloggy/posts.html')
def list_posts(paging_key):
    tag = request.args.get('tag', None)
    span = trace.get_current_span()
    span.set_attribute('bloggy.list_posts.tag', tag)
    if tag is not None and re.match(r'^[a-z0-9-_]+$', tag) is None:
        span.set_attribute('bloggy.input_validation_fail', 'list_posts.tag')
        return abort(400)
    posts, next_paging_key = get_db().get_published_posts(
        tag=tag, paging_key=paging_key
    )

    return dict(posts=posts), next_paging_key


@tracer.start_as_current_span('show_post')
@blueprint.get('/<slug>/')
def show_post(slug):
    span = trace.get_current_span()
    span.set_attribute('bloggy.show_post.slug', slug)
    post = get_db().get_published_post(slug=slug, on_not_found=_404)
    return render_template('bloggy/post.html', post=post)


@blueprint.get('/images/<path:location>')
def show_image(location):
    bloggy = current_app.extensions['bloggy']
    s3 = bloggy.s3
    width = bloggy.images_width
    height = bloggy.images_height
    buffer = s3.get_jpg(location=escape(location), width=width, height=height,
                        on_not_found=_404)
    response = make_response()
    response.headers['Content-Type'] = 'image/jpeg'
    response.data = buffer.getvalue()
    response.headers['Cache-Control'] = 'max-age=315360000, public, immutable'
    return response
