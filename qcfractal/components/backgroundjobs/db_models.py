import datetime

from sqlalchemy import Column, Integer, DateTime, String, JSON, Index

from qcfractal.db_socket import BaseORM


class BackgroundJobORM(BaseORM):
    __tablename__ = "background_jobs"

    id = Column(Integer, primary_key=True)
    added_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    started_date = Column(DateTime)
    ended_date = Column(DateTime)

    function = Column(String, nullable=False)
    args = Column(JSON, nullable=False)
    kwargs = Column(JSON, nullable=False)
    result = Column(JSON)
    user = Column(String)

    __table_args__ = (
        Index("ix_background_jobs_added_date", "added_date"),
    )
