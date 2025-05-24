import os
import re
import random
import aiohttp
import aiofiles
import asyncio
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from pytubefix import Playlist, YouTube, Search
from datetime import timedelta
from io import BytesIO
from playwright.async_api import async_playwright as PlayWright

class YTHM:
    def __init__(self, output_dir="downloads", cache_dir="cache", font_dir="assets"):
        self.output_dir = output_dir
        self.cache_dir = cache_dir
        self.font_dir = font_dir
        self.app = 'Mirza Bot'

        for path in [self.output_dir, self.cache_dir]:
            if not os.path.exists(path):
                os.makedirs(path)

    async def _thumbnail(self, video_id):

        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            yt = YouTube(url)

            name = yt.title or "Unknown Title"
            artist = yt.author or "Unknown Channel"
            totalDuration = yt.length or 0
            image_url = yt.thumbnail_url

            display_title = unidecode(" ".join(name.split(" ")[:12]))

            tmp_dir = Path("tmp")
            tmp_dir.mkdir(exist_ok=True)

            match = re.search(r'/vi/([^/]+)/', image_url)
            if not match:
                raise ValueError("Invalid image URL")
            extracted_id = match.group(1)

            tmp_path = tmp_dir / f"tmp_{extracted_id}.png"

            if tmp_path.exists() and time.time() - tmp_path.stat().st_mtime < 3600:
                output = tmp_path.open("rb")
                output.name = tmp_path.name
                return output

            now = time.time()
            for file in tmp_dir.glob("tmp_*.png"):
                if now - file.stat().st_mtime > 3600:
                    try: file.unlink()
                    except: pass

            thumb_local = tmp_dir / f"thumb_{extracted_id}.jpg"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            async with aiofiles.open(thumb_local, mode="wb") as f:
                                await f.write(await resp.read())
            except Exception as e:
                raise RuntimeError(f"Failed to download image: {e}")

            current_sec = random.randint(0, totalDuration)
            current = f"{current_sec // 60:02}:{current_sec % 60:02}"
            duration = f"{totalDuration // 60:02}:{totalDuration % 60:02}"

            async with PlayWright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(
                    f"file:///home/ubuntu/devbot/index.html?song={name}&artist={artist}&duration={duration}&current={current}&app={self.app}&image={thumb_local.absolute()}"
                )
                await page.wait_for_timeout(1000)
                buffer = await page.screenshot(full_page=True)
                await browser.close()

            img = Image.open(BytesIO(buffer))
            cropped_img = img.crop((420, 75, img.width - 420, img.height - 75))
            cropped_img.save(tmp_path, format='PNG')

            output = tmp_path.open("rb")
            output.name = tmp_path.name
            return output

        except Exception as e:
            print(f"[X] Failed to generate thumbnail: {e}")
            return None


    def _sanitize_filename(self, title):
        return re.sub(r'[\\/*?:"<>|]', "_", title).replace(" ", "_")

    def _details(self, video_id: str) -> dict:
        """
        Get metadata details of a YouTube video using its ID.
        :param video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ')
        :return: Dict with video metadata
        """
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            yt = YouTube(url)

            return {
                "title": yt.title,
                "channel": yt.author,
                "length_sec": yt.length,
                "length_min": round(yt.length / 60, 2),
                "views": yt.views,
                "publish_date": yt.publish_date.strftime('%Y-%m-%d') if yt.publish_date else None,
                "description": yt.description,
                "keywords": yt.keywords,
                "thumbnail_url": yt.thumbnail_url,
                "video_url": url,
            }

        except Exception as e:
            print(f"[X] Failed to fetch video details: {e}")
            return {}

    def _search(self, query: str) -> str:
        """
        Search YouTube and return the video ID of the top result.
        :param query: Search string (e.g., "mirza song")
        :return: YouTube video ID string (e.g., 'dQw4w9WgXcQ')
        """
        try:
            search = Search(query)
            result = search.videos[0]
            video_id = result.video_id
            print(f"[+] Search result: {result.title} ({video_id})")
            return video_id
        except Exception as e:
            print(f"[X] Search failed: {e}")
            return None

    def _mp3(self, watch_id: str):
        """
        Download MP3 from a YouTube video, or return existing path if already downloaded.
        """
        url = f"https://www.youtube.com/watch?v={watch_id}"
        yt = YouTube(url)
        filename = self._sanitize_filename(yt.title)
        base_path = os.path.join(self.output_dir, filename)
        mp3_path = base_path + '.mp3'

        if os.path.exists(mp3_path):
            print(f"[✓] MP3 already exists: {mp3_path}")
            return mp3_path

        print(f"[+] Title: {yt.title}")
        print(f"[+] Channel: {yt.author}")
        print(f"[+] Fetching audio stream...")

        stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        if not stream:
            raise Exception("No audio stream found.")

        print(f"[+] Downloading to: {self.output_dir}")
        output_file = stream.download(output_path=self.output_dir, filename=filename + ".webm")

        os.rename(output_file, mp3_path)
        print(f"[+] Saved MP3: {mp3_path}")
        return mp3_path


    def _mp4(self, watch_id: str):
        """
        Download MP4 from a YouTube video, or return existing path if already downloaded.
        """
        url = f"https://www.youtube.com/watch?v={watch_id}"
        yt = YouTube(url)
        filename = self._sanitize_filename(yt.title)
        mp4_path = os.path.join(self.output_dir, filename + ".mp4")

        if os.path.exists(mp4_path):
            print(f"[✓] MP4 already exists: {mp4_path}")
            return mp4_path

        print(f"[+] Title: {yt.title}")
        print(f"[+] Channel: {yt.author}")
        print(f"[+] Fetching best MP4 stream...")

        stream = yt.streams.filter(progressive=True, file_extension='mp4')\
                        .order_by('resolution')\
                        .desc()\
                        .first()
        if not stream:
            raise Exception("No MP4 stream found.")

        print(f"[+] Downloading to: {self.output_dir}")
        mp4_path = stream.download(output_path=self.output_dir, filename=filename + ".mp4")

        print(f"[+] Saved MP4: {mp4_path}")
        return mp4_path

    def _playlist(self, playlist_id: str, max_tracks=25, format="mp3"):
        """
        Download MP3 or MP4 files from a YouTube playlist, skipping existing ones.
        """
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        pl = Playlist(playlist_url)

        print(f"[+] Playlist title: {pl.title}")

        try:
            all_urls = list(pl.video_urls)
        except Exception as e:
            print(f"[!] Failed to fetch playlist URLs: {e}")
            return

        print(f"[+] Total videos in playlist: {len(all_urls)}")

        for i, video_url in enumerate(all_urls[:max_tracks]):
            try:
                yt = YouTube(video_url)
                filename = yt.title.replace(" ", "_").replace("/", "_")
                print(f"\n[#{i + 1}] Checking: {yt.title}")

                if format == "mp3":
                    final_path = os.path.join(self.output_dir, filename + ".mp3")
                elif format == "mp4":
                    final_path = os.path.join(self.output_dir, filename + ".mp4")
                else:
                    print(f"[!] Invalid format: {format}")
                    continue

                if os.path.exists(final_path):
                    print(f"[✓] Already downloaded: {final_path}")
                    continue

                print(f"[+] Downloading: {yt.title}")

                if format == "mp3":
                    stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
                    temp_file = stream.download(output_path=self.output_dir, filename=filename + ".webm")
                    os.rename(temp_file, final_path)

                elif format == "mp4":
                    stream = yt.streams.filter(progressive=True, file_extension='mp4')\
                                    .order_by('resolution')\
                                    .desc()\
                                    .first()
                    stream.download(output_path=self.output_dir, filename=filename + ".mp4")

                print(f"[+] Saved {format.upper()}: {final_path}")

            except Exception as e:
                print(f"[X] Failed to process video #{i + 1}: {e}")


# === USAGE ===

youtube = YTHM(output_dir="downloads")

# Download a single MP3
# path = youtube._mp3("NT18JMqGhyg")
# print(path)
# Download a single MP4
# youtube._mp4("NT18JMqGhyg")

# Download an entire playlist in MP3 or MP4
# youtube._playlist("PLBbzFWh6HcrxenSSeA5qJ97UUbafvudy5", format="mp4")

# Search youtube with query to get video ID
# info = youtube._search("Mirza Song")
# print(info)

# Search youtube with query to get video ID
# info = youtube._details("NT18JMqGhyg")
# print(info)

# thumb_path = asyncio.run(youtube._thumbnail("pv9yYF5GrWg"))
# print("Thumbnail generated at:", thumb_path)
