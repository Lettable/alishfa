import asyncio
import logging
import time
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, FloodWait
from pyrogram.types import BotCommand
from config import API_ID, API_HASH, BOT_TOKEN
import config

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
    datefmt="%d-%b-%y %H:%M:%S",
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)


app = Client(
    "Lettable",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

mirza = Client(
    "Mirza",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION
)

mirza2 = Client(
    "Mirza2",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION2
)

mirza3 = Client(
    "Mirza3",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION3
)

boot = time.time()
async def austinOG():
    try:
        await app.start()
        await mirza.start()
        await mirza2.start()
        await mirza3.start()
        await asyncio.sleep(2)
    except FloodWait as ex:
        LOGGER.warning(ex)
        await asyncio.sleep(ex.value)

    print(1)
    try:   
        LOGGER.info(f"Bot Started As {app.me.first_name}")
    except Exception as e:
        print(e)
        exit()

asyncio.get_event_loop().run_until_complete(austinOG())
