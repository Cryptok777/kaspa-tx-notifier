# encoding: utf-8
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup


def get_message_text(address, amount, tx_id):
    short_address = address[:24] + "..." + address[-6:]
    return (
        f"🔔 Address: <b><a href='https://kas.fyi/address/{address}'>{short_address}</a></b>\n"
        f"💰 Amount: <a href='https://kas.fyi/transaction/{tx_id}'>{int(amount) / 1e8} KAS</a>\n\n"
        f"🛑 To stop this monitor, reply: <code>/stop {address}</code>"
    )


async def start(kaspad_client, bot_client, subscribe_service):
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
                pass

                print(f"sending {message}")
                text_message = get_message_text(
                    message["address"], message["amount"], message["tx_id"]
                )

                await bot_client.send_message(
                    chat_id=message["chat_id"],
                    text=text_message,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )

        except KeyError:
            return

    await kaspad_client.notify("notifyBlockAddedRequest", None, on_new_block)
