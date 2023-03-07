import asyncio
import logging
import os
from SubscribeService import SubscribeService
from dotenv import load_dotenv

from dbsession import create_all
from kaspad.KaspadMultiClient import KaspadMultiClient
from sockets import blocks

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

load_dotenv(override=True)

logging.basicConfig(
    format="%(asctime)s::%(levelname)s::%(name)s::%(message)s",
    level=logging.DEBUG if os.getenv("DEBUG", False) else logging.INFO,
    handlers=[logging.StreamHandler()],
)

logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
_logger = logging.getLogger(__name__)

create_all(drop=False)

router = Router()

kaspad_hosts = []

for i in range(100):
    try:
        kaspad_hosts.append(os.environ[f"KASPAD_HOST_{i + 1}"].strip())
    except KeyError:
        break

if not kaspad_hosts:
    raise Exception("Please set at least KASPAD_HOST_1 environment variable.")

# create Kaspad client
client = KaspadMultiClient(kaspad_hosts)
task_runner = None

# db
subscribe_service = SubscribeService()


def verify_param(message, short=False):
    command_body = message.text.split(" ")
    if (len(command_body)) != 2:
        raise Exception("Wrong command!")
    address = command_body[1].strip().lower()
    if short and not address.startswith("kaspa"):
        address = "kaspa:" + address
    if not address.startswith("kaspa"):
        raise Exception("Invalid address")

    return address


async def handle_subscribe(message: types.Message, address: str, chat_id: int):
    res = subscribe_service.subscribe(chat_id=chat_id, address=address)
    if res:
        await message.answer(f"You've started monitoring {address}")
    else:
        await message.answer(
            f"Failed to start monitoring {address}, you may have already set up a monitor for that address"
        )


async def handle_unsubscribe(message: types.Message, address: str, chat_id: int):
    res = subscribe_service.unsubscribe(chat_id=chat_id, address=address)
    if res:
        await message.answer(f"You've stopped monitoring {address}")
    else:
        await message.answer(f"Failed to stop monitoring {address}")


async def handle_unsubscribe_all(message: types.Message, chat_id: int):
    res = subscribe_service.unsubscribe_all(
        chat_id=chat_id,
    )
    if res:
        await message.answer(f"You've stopped monitoring all addresses")
    else:
        await message.answer(f"Failed to stop monitoring addresses")


@router.message(CommandStart())
async def start_handler(message: types.Message) -> None:
    chat_id = message.chat.id
    try:
        address = verify_param(message, short=True)
        await handle_subscribe(message=message, address=address, chat_id=chat_id)
    except Exception as e:
        _logger.error(e)
        await message.answer("Something went wrong!")


@router.message(Command(commands=["stop"]))
async def unsubscribe_handler(message: types.Message) -> None:
    chat_id = message.chat.id
    try:
        address = verify_param(message)
        await handle_unsubscribe(message=message, address=address, chat_id=chat_id)
    except Exception as e:
        _logger.error(e)
        await message.answer("Something went wrong!")


@router.message(Command(commands=["stop_all"]))
async def unsubscribe_all_handler(message: types.Message) -> None:
    chat_id = message.chat.id
    try:
        await handle_unsubscribe_all(message=message, chat_id=chat_id)
    except Exception as e:
        _logger.error(e)
        await message.answer("Something went wrong!")


@router.message(Command(commands=["list"]))
async def list_handler(message: types.Message) -> None:
    chat_id = message.chat.id
    try:
        res = subscribe_service.get_addresses_for_chat_id(
            chat_id=chat_id,
        )
        reply_message = "\n\n".join(
            [
                f"<a href='https://kas.fyi/address/{address}'>{address}</a>"
                for address in res
            ]
        )
        reply_message += f"\n\n🛑 To stop any monitor, reply: <code>/stop ADDRESS</code>"
        await message.answer(
            reply_message if res else "You are not monitoring any address right now",
            disable_web_page_preview=True,
        )
    except Exception as e:
        _logger.error(e)
        await message.answer("Something went wrong!")


async def main():
    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"], parse_mode="HTML")

    await client.initialize_all()
    asyncio.create_task(blocks.start(client, bot, subscribe_service))
    await asyncio.create_task(dp.start_polling(bot))

    # async with asyncio.TaskGroup() as tg:
    #     tg.create_task(dp.start_polling(bot))


if __name__ == "__main__":
    asyncio.run(main())
