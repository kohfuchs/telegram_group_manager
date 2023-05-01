from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import create_engine
import datetime

engine = create_engine("sqlite:////db/GROUP_MANAGER.db")

class Base(DeclarativeBase):
    pass

class Groups(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_name: Mapped[str]
    group_id: Mapped[int]
    group_joined: Mapped[datetime.datetime]
    group_active: Mapped[bool]
    group_deleted: Mapped[bool]


Base.metadata.create_all(engine)