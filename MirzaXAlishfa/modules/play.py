from pyrogram import filters
from MirzaXAlishfa import app, mirza
from MirzaXAlishfa.helper.song import YTHM
from typing import List, Dict

youtube = YTHM(output_dir="downloads")

# Download a single MP3
# youtube._mp3("NT18JMqGhyg")

# Download a single MP4
# youtube._mp4("NT18JMqGhyg")

# Download an entire playlist in MP3 or MP4
# youtube._playlist("PLBbzFWh6HcrxenSSeA5qJ97UUbafvudy5", format="mp4")

# Search youtube with query to get video ID
# info = youtube._search("Mirza Song")
# print(info)

# Search youtube with query to get video ID
# info = youtube._details("pv9yYF5GrWg")
# print(info)

# thumb_path = asyncio.run(youtube._thumbnail("pv9yYF5GrWg"))
# print("Thumbnail generated at:", thumb_path)
