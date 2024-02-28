import base64
import uuid

import cv2
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base


class Base(declarative_base()):

    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    def __init__(self):
        self.id = uuid.uuid4()

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
