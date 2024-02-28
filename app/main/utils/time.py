from datetime import datetime, timedelta


MINS_PER_HOUR = SECS_PER_MIN = 60
MILLIS_PER_SEC = 1000


def string_to_time(s, format='%H:%M:%S.%f'):
    return datetime.strptime(s, format).time()


def int_to_time(i):
    return string_to_time(str(timedelta(seconds=i)), format='%H:%M:%S')


def time_to_millis(t):
    return (t.hour * MINS_PER_HOUR * SECS_PER_MIN * MILLIS_PER_SEC) + \
           (t.minute * SECS_PER_MIN * MILLIS_PER_SEC) + \
           (t.second * MILLIS_PER_SEC) + \
           (t.microsecond / MILLIS_PER_SEC)


def time_to_seconds(t):
    return time_to_millis(t) / MILLIS_PER_SEC
