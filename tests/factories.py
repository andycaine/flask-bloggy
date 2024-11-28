import factory

from flask_bloggy import events, models


class ImageFactory(factory.Factory):
    class Meta:
        model = models.Image
    desc = factory.Faker('sentence', nb_words=5)
    title = factory.Faker('sentence', nb_words=5)
    location = factory.Sequence(lambda n: 'bucket/image-%d' % n)


class TagFactory(factory.Factory):
    class Meta:
        model = models.Tag
    name = factory.Sequence(lambda n: 'tag-%d' % n)
    label = factory.Sequence(lambda n: 'Tag %d' % n)


class PostFactory(factory.Factory):
    class Meta:
        model = models.Post
    slug = factory.Sequence(lambda n: 'post-%d' % n)
    title = factory.Sequence(lambda n: 'Post %d' % n)
    body = factory.Faker('sentence', nb_words=100)
    created = factory.Faker('date_time')
    main_image = factory.SubFactory(ImageFactory)
    tags = factory.LazyFunction(lambda: {TagFactory() for _ in range(3)})


class EventPostFactory(PostFactory):
    class Meta:
        model = events.Post

    published = factory.Faker('pybool')
    tags = factory.LazyFunction(lambda: {f'tag{i}' for i in range(3)})
