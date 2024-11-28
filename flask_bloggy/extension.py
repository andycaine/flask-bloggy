from flask import url_for
from markupsafe import Markup

from . import db
from . import filters
from . import s3
from .blueprint import blueprint


class BloggyExtension:

    def __init__(self, table_name, images_bucket_name, images_width,
                 images_height, url_prefix='/posts', app=None):
        self.url_prefix = url_prefix
        self.table_name = table_name
        self.images_bucket_name = images_bucket_name
        self.images_width = images_width
        self.images_height = images_height
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.db = db.Database(self.table_name)
        self.s3 = s3.S3(bucket_name=self.images_bucket_name)
        app.register_blueprint(blueprint, url_prefix=self.url_prefix)

        app.template_filter('md_to_html')(filters.md_to_html)
        app.template_filter('first_para')(filters.first_para)

        @app.context_processor
        def image_tag_builder():
            def inner(img):
                url = url_for('bloggy.show_image', location=img.location)
                return Markup(
                    '<img'
                    f' src="{url}"'
                    f' width="{self.images_width}"'
                    f' height="{self.images_height}"'
                    f' alt="{img.desc}"'
                    f' title="{img.title}"'
                    '/>'
                )
            return dict(image=inner)

        app.extensions['bloggy'] = self
