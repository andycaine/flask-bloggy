from flask import Flask
from .extension import BloggyExtension


__all__ = ['create_app']


def create_app():
    app = Flask(__name__)
    app.config.from_prefixed_env(prefix='BLOGGY')

    BloggyExtension(
        app=app,
        table_name=app.config['TABLE_NAME'],
        images_bucket_name=app.config['IMAGES_BUCKET_NAME'],
        images_width=1300,
        images_height=450
    )

    return app


def run():
    create_app().run(port=8080, debug=True)
