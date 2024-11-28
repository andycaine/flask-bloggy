import opentelemetry
import opentelemetry.trace


def set_attr(attr, value):
    opentelemetry.trace.get_current_span().set_attribute(attr, value)
