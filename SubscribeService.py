from dbsession import session_maker
from models.SubscribedAddress import SubscribedAddress
from sqlalchemy.sql import func


class SubscribeService:
    def __init__(self):
        self.db_session = session_maker()

    def subscribe(self, chat_id: int, address: str):
        new_sub = SubscribedAddress(
            address=address, chat_id=chat_id, created_at=func.now(), deleted=False
        )
        try:
            self.db_session.merge(new_sub)
            self.db_session.commit()
            return True
        except:
            return False

    def unsubscribe(self, chat_id: int, address: str):
        row = (
            self.db_session.query(SubscribedAddress)
            .filter(
                SubscribedAddress.address == address,
                SubscribedAddress.chat_id == chat_id,
            )
            .update({"deleted": True})
        )
        self.db_session.commit()
        return True if row > 0 else False

    def unsubscribe_all(self, chat_id: int):
        row = (
            self.db_session.query(SubscribedAddress)
            .filter(
                SubscribedAddress.chat_id == chat_id,
            )
            .update({"deleted": True})
        )
        self.db_session.commit()
        return True if row > 0 else False

    def get_chat_ids_for_address(self, address: str):
        chat_id_rows = (
            self.db_session.query(SubscribedAddress)
            .where(
                SubscribedAddress.address == address, SubscribedAddress.deleted == False
            )
            .all()
        )
        return [row.chat_id for row in chat_id_rows]
