from datetime import datetime, timedelta


def days_ago(n):
    return datetime.now() - timedelta(days=n)
