from sqlalchemy import Column, String, TIMESTAMP, Integer, Boolean

from dbsession import Base


class SubscribedAddress(Base):
    __tablename__ = "subscribed_addresses"
    address = Column(String, primary_key=True)
    chat_id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=False))
    deleted = Column(Boolean, default=False)
