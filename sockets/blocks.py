# encoding: utf-8
import logging
import time
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.types.inline_keyboard_button import InlineKeyboardButton


_logger = logging.getLogger(__name__)


def get_message_text(address, amount, tx_id):
    short_address = address[:24] + "..." + address[-6:]
    return (
        f"🔔 Address: <b><a href='https://kas.fyi/address/{address}'>{short_address}</a></b>\n"
        f"💰 Amount: <a href='https://kas.fyi/transaction/{tx_id}'>{int(amount) / 1e8} KAS</a>"
    )


global local_cache
CLEAR_HASHES_TIMEOUT = 60


def get_message_hash(address: str, tx_id: str, chat_id: int):
    return f"{address}-{tx_id}-{chat_id}"


async def start(kaspad_client, bot_client, subscribe_service):
    local_cache = {"sent_hashes": set(), "last_clear_sent_hashes_at": time.time()}

    async def on_new_block(e):
        try:
            block_info = e["blockAddedNotification"]["block"]
            pending_messages = []
            for tx in block_info["transactions"]:
                for output in tx["outputs"]:
                    address = output["verboseData"]["scriptPublicKeyAddress"]
                    amount = output["amount"]
                    tx_id = tx["verboseData"]["transactionId"]
                    target_chat_ids = subscribe_service.get_chat_ids_for_address(
                        address
                    )
                    for chat_id in target_chat_ids:
                        pending_messages.append(
                            {
                                "address": address,
                                "amount": amount,
                                "tx_id": tx_id,
                                "chat_id": chat_id,
                            }
                        )

            for message in pending_messages:
                message_hash = get_message_hash(
                    address=message["address"],
                    tx_id=message["tx_id"],
                    chat_id=message["chat_id"],
                )
                if message_hash not in local_cache["sent_hashes"]:
                    _logger.debug(f"sending message to {message['chat_id']}")
                    text_message = get_message_text(
                        message["address"], message["amount"], message["tx_id"]
                    )

                    await bot_client.send_message(
                        chat_id=message["chat_id"],
                        text=text_message,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="Stop Watching",
                                        callback_data=f"{message['address'][6:]}",
                                    )
                                ]
                            ]
                        ),
                    )
                    local_cache["sent_hashes"].add(message_hash)

            if (
                time.time()
                >= local_cache["last_clear_sent_hashes_at"] + CLEAR_HASHES_TIMEOUT
            ):
                local_cache["sent_hashes"].clear()
                local_cache["last_clear_sent_hashes_at"] = time.time()
                _logger.debug(f"Cleared local cache")

        except Exception as e:
            _logger.error(f"Error in on_new_block, {e}")

    await kaspad_client.notify("notifyBlockAddedRequest", None, on_new_block)
