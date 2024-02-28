import sqlalchemy.types as types


class IntEnum(types.TypeDecorator):

    impl = types.Integer

    def __init__(self, enumType, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enumType = enumType

    def process_bind_param(self, value, dialect):
        # ensures int values are stored in db instead of enum text values
        if isinstance(value, int):
            return value

        return value.value

    def process_result_value(self, value, dialect):
        # called after db query to construct enum type
        return self.enumType(value)
