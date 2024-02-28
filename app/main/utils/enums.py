import enum


class TranscriptType(enum.Enum):

    NO_TYPE = 0
    MANUAL = 1
    AUTO = 2


class Gender(enum.Enum):

    NO_TYPE = 0
    MALE = 1
    FEMALE = 2


class HeadPoseDirection(enum.Enum):

    NO_TYPE = 0
    UPPER_LEFT = 1
    UPPER_CENTRE = 2
    UPPER_RIGHT = 3
    CENTRE_LEFT = 4
    CENTRE = 5
    CENTRE_RIGHT = 6
    LOWER_LEFT = 7
    LOWER_CENTRE = 8
    LOWER_RIGHT = 9

    @staticmethod
    def get(text):
        return getattr(HeadPoseDirection, '_'.join(text.upper().split(' ')))
