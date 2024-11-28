import io
import math

import boto3
import botocore.exceptions
from PIL import Image


class ImageResizer:

    def __init__(self, image, size):
        self.image = image
        self.width, self.height = size

    def resize(self):
        self.scale()
        return self.crop()

    def scale(self):
        self.image = self.image.resize(
            (self.scaled_width(), self.scaled_height()),
            Image.LANCZOS
        )

    def scaled(self, dimension):
        return int(math.ceil(dimension * self.resize_ratio()))

    def scaled_height(self):
        return self.scaled(self.image_height())

    def scaled_width(self):
        return self.scaled(self.image_width())

    def resize_ratio(self):
        return max(self.width / float(self.image_width()),
                   self.height / float(self.image_height()))

    def crop(self):
        x_offset = self.half_width_delta()
        y_offset = self.half_height_delta()

        return self.image.crop((x_offset,
                                y_offset,
                                self.width + x_offset,
                                self.height + y_offset))

    def half_width_delta(self):
        return self.half(self.image_width() - self.width)

    def half_height_delta(self):
        return self.half(self.image_height() - self.height)

    def half(self, x):
        return int(x / 2.0)

    def width_delta(self):
        return self.image_width() - self.width

    def image_width(self):
        return self.image.size[0]

    def image_height(self):
        return self.image.size[1]


class S3:

    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3')

    def get_jpg(self, location, width, height, on_not_found=None):
        try:
            response = self.s3.get_object(Bucket=self.bucket_name,
                                          Key=location)

            obj = response['Body'].read()
            img = Image.open(io.BytesIO(obj))

            resizer = ImageResizer(img, (width, height))
            img = resizer.resize()

            buffer = io.BytesIO()
            img.save(buffer, 'JPEG', quality=80)

            return buffer
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                on_not_found()
            else:
                raise e
