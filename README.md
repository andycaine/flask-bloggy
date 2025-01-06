# flask-bloggy

A simple but fast blog extension for flask.

## Getting started

Install using pip:

```bash
pip install flask-bloggy
```

Then add as an extension to a flask app:

```python
from flask import Flask
from flask_bloggy import BloggyExtension

app = Flask(__name__)

BloggyExtension(app=app,
                table_name='dynamodb-table',
                images_bucket_name='s3-bucket-name',
                images_width=1300,
                images_height=450
                url_prefix='/posts')

```
