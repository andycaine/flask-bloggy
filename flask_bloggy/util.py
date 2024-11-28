from boto3.dynamodb.types import TypeDeserializer, TypeSerializer


deserializer = TypeDeserializer()
serializer = TypeSerializer()


def dynamodb_to_dict(dynamo_obj):
    return {
        k: deserializer.deserialize(v)
        for k, v in dynamo_obj.items()
    }


def dict_to_dynamodb(data):
    return {
        k: serializer.serialize(v)
        for k, v in data.items()
    }
