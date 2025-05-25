import asyncio
import config
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ChatType
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import random
import aiohttp
from io import BytesIO
from pyrogram.raw.functions.messages import Report
from pyrogram.raw.functions.account import ReportPeer
from pyrogram.raw.types import InputReportReasonChildAbuse, InputReportReasonCopyright, InputReportReasonFake, InputReportReasonGeoIrrelevant, InputReportReasonIllegalDrugs, InputReportReasonPersonalDetails, InputReportReasonPornography, InputReportReasonSpam, InputReportReasonViolence
from pyrogram.raw.types import InputPeerUser, InputPeerChannel, InputPeerChat
from pyrogram.errors import FloodWait, RPCError
from pyrogram.raw.functions.account import CheckUsername as AccountCheckUsername
from pyrogram.errors import UsernameNotOccupied, UsernameInvalid
import logging
from pyrogram.raw.types import ReportResultAddComment
import json
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
import subprocess

from MirzaXAlishfa import mirza, mirza2, mirza3, app

niggers = [mirza, mirza2, mirza3]

logging.basicConfig(level=logging.INFO)

REASON_CODES = {
    "Custom": 1,
    "Abuse": 2,
    "Violence": 3,
    "Goods": {
        "Weapons": 41,
        "Drugs": 42,
        "Fake documents": 43,
        "Counterfeit money": 44,
        "Other goods": 45
    },
    "Content": {
        "Child abuse": 51,
        "Non-consensual sexual imagery": 52,
        "Other illegal sexual content": 53
    },
    "Personal": {
        "Private images": 61,
        "Phone number": 62,
        "Address": 63,
        "Other personal information": 64
    },
    "Terrorism": 7,
    "Scam": {
        "Phishing": 81,
        "Impersonation": 82,
        "Fraudulent sales": 83,
        "Spam": 84
    },
    "Copyright": 9
}

DATA_FILE = "/home/ubuntu/devbot/data.json"
MUTATED_DIR = "mutated_videos"
os.makedirs(MUTATED_DIR, exist_ok=True)

data = {
  "Catogs": [
    { "Name": "catog1", "Prefix": "ct_1" },
    { "Name": "catog2", "Prefix": "ct_2" },
    { "Name": "catog3", "Prefix": "ct_3" },
    { "Name": "catog4", "Prefix": "ct_4" }
  ],
  "Video": [
    { "Name": "VideoName1", "path": "/home/austin/video/video1.mp4", "catog": "ct_1" },
    { "Name": "VideoName2", "path": "/home/austin/video/video2.mp4", "catog": "ct_4" },
    { "Name": "VideoName3", "path": "/home/austin/video/video3.mp4", "catog": "ct_2" },
    { "Name": "VideoName4", "path": "/home/austin/video/video4.mp4", "catog": "ct_3" },
    { "Name": "VideoName5", "path": "/home/austin/video/video5.mp4", "catog": "ct_1" }
  ]
}


catogs = data["Catogs"]
videos = data["Video"]

catog_map = {entry["Prefix"]: entry["Name"] for entry in catogs}

progress = {}

PAGE_SIZE = 10

user_data = {}
reports = {}

peer_reason = {
    "Abuse": InputReportReasonChildAbuse(),
    "Copyright": InputReportReasonCopyright(),
    "Fake": InputReportReasonFake(),
    "Terrorism": InputReportReasonGeoIrrelevant(),
    "Drugs": InputReportReasonIllegalDrugs(),
    "Personal": InputReportReasonPersonalDetails(),
    "Pornography": InputReportReasonPornography(),
    "Spam": InputReportReasonSpam(),
    "Violence": InputReportReasonViolence(),
}

def progress_bar(done, total):
    blocks = 20
    filled = int((done / total) * blocks)
    return "▓" * filled + "░" * (blocks - filled)

class VideoMutator:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path

    def random_time_segment(self, base_start, base_end, jitter=0.3):
        start = max(0, base_start + random.uniform(-jitter, jitter))
        end = max(start + 0.1, base_end + random.uniform(-jitter, jitter))
        return round(start, 3), round(end, 3)

    def random_padding(self, base_pad=4, jitter=2):
        pad_w = base_pad + random.randint(-jitter, jitter)
        pad_w = max(1, pad_w)
        return pad_w

    def random_framestep(self, base_step=2, jitter=1):
        step = base_step + random.randint(-jitter, jitter)
        return max(1, step)

    def mutate(self):
        noise1_start, noise1_end = self.random_time_segment(9.2, 9.7)
        noise2_start, noise2_end = self.random_time_segment(4.19, 4.81)
        noise3_start, noise3_end = self.random_time_segment(12.96, 13.32)

        pad_size = self.random_padding()
        frame_step = self.random_framestep()

        filter_complex = (
            f"[0:v]split=2[main][glitch];"
            f"[glitch]framestep={frame_step},setpts=N/FRAME_RATE/TB[glitch2];"
            f"[main][glitch2]blend=all_mode=average[mixed];"
            f"[mixed]pad=iw+{pad_size}:ih+{pad_size}:{pad_size//2}:{pad_size//2}:color=black,"
            f"setpts=1.02*PTS,minterpolate=fps=20:mi_mode=mci:mc_mode=aobmc:vsbmc=1[videoout];"
            f"[1:a]atrim=start={noise1_start}:end={noise1_end},asetpts=PTS-STARTPTS[noise1];"
            f"[1:a]atrim=start={noise2_start}:end={noise2_end},asetpts=PTS-STARTPTS[noise2];"
            f"[1:a]atrim=start={noise3_start}:end={noise3_end},asetpts=PTS-STARTPTS[noise3];"
            f"[0:a]volume=1.1,adelay=80|80,highpass=f=250,lowpass=f=3500[base];"
            f"[base][noise1]amix=inputs=2:duration=first:dropout_transition=2[temp1];"
            f"[temp1][noise2]amix=inputs=2:duration=first:dropout_transition=2[temp2];"
            f"[temp2][noise3]amix=inputs=2:duration=first:dropout_transition=2[temp3];"
            f"[temp3]anull[audioout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", self.input_path,
            "-f", "lavfi", "-t", "14", "-i", "anoisesrc=color=white:amplitude=0.4",
            "-filter_complex", filter_complex,
            "-map", "[videoout]",
            "-map", "[audioout]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            self.output_path
        ]

        print("Running ffmpeg command:\n", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("ffmpeg error:\n", result.stderr)
            raise RuntimeError("ffmpeg command failed")

class Reporter:
    def __init__(self, app, user_id, report_data, message):
        self.app = app
        self.user_id = user_id
        self.data = report_data
        self.msg = message
        self.reason = random.choice(list(peer_reason.values()))
        self.text = self.data.get("comment") or "Abusive or inappropriate behavior."
        self.total = int(self.data.get("amount") or 0)
        self.done = 0
        self.message_reports = 0
        self.errors = []
        self.progress_msg_id = None

    async def run(self):
        start_time = time.time()
        try:
            progress_msg = await self.msg.reply_text(self._build_progress())
            self.progress_msg_id = progress_msg.id

            for i in range(self.total):
                anony = niggers[i % len(niggers)]
                peer_id = self.data.get("peer_id")

                peer_obj = await self._resolve_peer(anony, peer_id)
                if peer_obj is None:
                    await self.msg.reply_text("❌ Error: Peer could not be resolved.")
                    return

                report_peer = False
                report_messages = False

                try:
                    hoe = await anony.invoke(ReportPeer(
                        peer=peer_obj,
                        reason=self.reason,
                        message=self.text
                    ))
                    report_peer = True

                    message_ids = []
                    async for m in anony.search_messages(peer_id, limit=50):
                        if m and m.id:
                            message_ids.append(m.id)

                    if message_ids:
                        opts = self.data.get("reason")
                        option_bytes = opts if isinstance(opts, bytes) else str(opts).encode()


                        first_attempt = await anony.invoke(Report(
                            peer=peer_obj,
                            id=message_ids,
                            option=option_bytes,
                            message=self.text
                        ))

                        if isinstance(first_attempt, ReportResultAddComment):
                            second_attempt = await anony.invoke(Report(
                                peer=peer_obj,
                                id=message_ids,
                                option=first_attempt.option,
                                message=self.text
                            ))
                            print(f"✅ Report done on {len(message_ids)}!\n\n{message_ids}")
                            self.message_reports += len(message_ids)
                            report_messages = True
                        else:
                            print("✅ Report did not require comment.")
                            self.message_reports += len(message_ids)
                            report_messages = True
                            
                    
                    self.done += 1
                    await self._update_progress(start_time)

                except FloodWait as e:
                    await self._flood_wait(e)
                except RPCError as e:
                    await self._report_error_live(f"❌ RPCError on report {i + 1}: `{e}`")
                    self.errors.append(str(e))
                except Exception as e:
                    await self._report_error_live(f"❌ Unexpected error on report {i + 1}: `{e}`")
                    self.errors.append(str(e))

            await self._final_update()

        except Exception as e:
            await self.msg.reply_text(f"❌ Unhandled Error: {e}")

    async def _resolve_peer(self, anony, peer_id):
        try:
            peer_id = int(peer_id)
        except ValueError:
            await self.msg.reply_text("❌ Invalid Peer ID format.")
            return None

        try:
            await anony.join_chat(peer_id)
            try:
                return await anony.resolve_peer(peer_id)
            except Exception as e:
                print(f"[Resolve Error] {anony}: {e}")
                await asyncio.sleep(1)
        except Exception as e:
            print(f"[Join Error] {anony}: {e}")
            await asyncio.sleep(1)

        try:
            return await anony.resolve_peer(peer_id)
        except Exception as e:
            print(f"[Resolve Error] {anony}: {e}")
            await asyncio.sleep(1)
        return None

    async def _report_error_live(self, error_msg):
        try:
            await self.app.edit_message_text(
                chat_id=self.msg.chat.id,
                message_id=self.progress_msg_id,
                text=self._build_progress() + f"\n\n{error_msg}"
            )
        except Exception:
            await self.msg.reply_text(error_msg)

    async def _update_progress(self, start_time):
        elapsed = time.time() - start_time
        eta = int((elapsed / self.done) * (self.total - self.done)) if self.done else 0
        text = self._build_progress(eta)

        try:
            await self.app.edit_message_text(
                chat_id=self.msg.chat.id,
                message_id=self.progress_msg_id,
                text=text
            )
        except Exception as e:
            fallback_text = text + f"\n\n⚠️ Error updating progress: `{e}`"
            await self.msg.reply_text(fallback_text)

    async def _flood_wait(self, e):
        notice = f"⚠️ FloodWait triggered: Sleeping for {e.value} seconds..."
        try:
            await self.app.edit_message_text(
                chat_id=self.msg.chat.id,
                message_id=self.progress_msg_id,
                text=self._build_progress() + f"\n\n{notice}"
            )
        except Exception:
            pass
        await asyncio.sleep(e.value)

    def _build_progress(self, eta=None):
        eta_str = f"{eta} sec" if eta is not None else "Calculating..."
        target = self.data.get("peer_id")
        bar = progress_bar(self.done, self.total)

        return f"""🛡️ {self.total} Reports Running

🎯 Target: `{target}`
🚨 Reason: `{self.data.get("reason")}`
📝 Comment: `{self.text}`

📨 Message Reports: `{self.message_reports}`
⏳ ETA: {eta_str}
📊 Progress: {bar} {self.done}/{self.total}
"""

    async def _final_update(self):
        summary = f"""✅ All {self.total} reports completed.

📨 Total messages reported: `{self.message_reports}`"""

        if self.errors:
            summary += "\n\n⚠️ Errors Encountered:\n" + "\n".join(f"- {e}" for e in self.errors)

        try:
            await self.app.edit_message_text(
                chat_id=self.msg.chat.id,
                message_id=self.progress_msg_id,
                text=self._build_progress() + "\n\n" + summary
            )
        except Exception:
            await self.msg.reply_text(summary)


start_button = InlineKeyboardMarkup([
    [InlineKeyboardButton(text='Owner', user_id=6586350542)],
    [InlineKeyboardButton(text='Term', callback_data='term'),
     InlineKeyboardButton(text='..', callback_data='yourself')]
])

@app.on_message(filters.command('start') & filters.private)
async def startcmd(_, message: Message):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    await message.reply_text("She's ALive :love:!", reply_markup=start_button)

@app.on_callback_query(filters.regex('term'))
async def help_callback(_, query: CallbackQuery):
    await query.answer("Don't ASK")

@app.on_callback_query(filters.regex('yourself'))
async def back_callback(_, query: CallbackQuery):
    await query.answer("?/adw")

@app.on_message(filters.command("moon"))
async def startcmd(_, message: Message):
    buttons = chunk_buttons(catogs)
    await message.reply("Choose a category:", reply_markup=InlineKeyboardMarkup(buttons))

async def send_video_page(msg, vids, prefix, page=0):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = vids[start:end]
    buttons = []
    for i in range(0, len(chunk), 2):
        row = []
        for j in [i, i+1]:
            if j < len(chunk):
                v = chunk[j]
                label = v["Name"][:6] + "..."
                row.append(InlineKeyboardButton(label, callback_data=f"video_{prefix}_{start+j}"))
        buttons.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"nav_vid_{prefix}_{page-1}"))
    if end < len(vids):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"nav_vid_{prefix}_{page+1}"))
    if nav:
        buttons.append(nav)
    await msg.edit(f"Videos in {catog_map[prefix]}", reply_markup=InlineKeyboardMarkup(buttons))

def chunk_buttons(items, page=0):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = items[start:end]
    buttons = []
    for i in range(0, len(chunk), 2):
        row = [InlineKeyboardButton(chunk[i]["Name"], callback_data=f"catog_{chunk[i]['Prefix']}")]
        if i + 1 < len(chunk):
            row.append(InlineKeyboardButton(chunk[i]["Name"], callback_data=f"catog_{chunk[i]['Prefix']}"))
        buttons.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Back", callback_data=f"nav_cat_{page-1}"))
    if end < len(items):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"nav_cat_{page+1}"))
    if nav:
        buttons.append(nav)
    return buttons

@app.on_message(filters.text & ~filters.regex(r"^/"))
async def handle_input(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id in reports:
        rep = reports[user_id]
        step = rep["step"]

        if step in ("peer_amount"):
            try:
                amount = int(text)
                limit = 50000
                if 0 <= amount <= limit:
                    rep["amount"] = amount
                    rep["step"] = "awaiting_target_type"
                    await message.reply(
                        "What are you reporting?",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Channel", callback_data="target_channel"),
                             InlineKeyboardButton("Group",  callback_data="target_group")]
                        ])
                    )
                else:
                    await message.reply(f"❌ Choose between 0 and {limit}.")
            except ValueError:
                await message.reply("❌ Send a valid number.")
            return

        if step == "awaiting_invite_link":
            rep["invite_link"] = text
            all_joined = True
            got_peer_id = False

            for omg in niggers:
                try:
                    sigma = await omg.join_chat(text)
                    rep["peer_id"] = sigma.id
                    got_peer_id = True
                except Exception as e:
                    if "USER_ALREADY_PARTICIPANT" in str(e):
                        try:
                            uwu = await omg.get_chat(text)
                            rep["peer_id"] = uwu.id
                            got_peer_id = True
                        except Exception as ine:
                            await message.reply(f"Error fetching chat after already joined: {ine}")
                        continue
                    else:
                        all_joined = False
                        await message.reply(f"Error with one client: {e}")
                        continue

            if got_peer_id:
                rep["step"] = "awaiting_comment"
                await message.reply(
                    "Choose report reason:",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("Child abuse", callback_data="report:final:2"),
                            InlineKeyboardButton("Violence", callback_data="report:final:3")
                        ],
                        [
                            InlineKeyboardButton("Illegal goods", callback_data="report:reason:Goods"),
                            InlineKeyboardButton("Illegal content", callback_data="report:reason:Content")
                        ],
                        [
                            InlineKeyboardButton("Personal data", callback_data="report:reason:Personal"),
                            InlineKeyboardButton("Terrorism", callback_data="report:final:7")
                        ],
                        [
                            InlineKeyboardButton("Scam or spam", callback_data="report:reason:Scam"),
                            InlineKeyboardButton("Copyright", callback_data="report:final:9")
                        ],
                        [
                            InlineKeyboardButton("I don’t like it", callback_data="report:final:1")
                        ]
                    ])
                )
            else:
                rep["step"] = "awaiting_chat_username"
                await message.reply("Could not auto-resolve Peer ID. Please send the Peer ID manually.")



        if step == "awaiting_chat_username":
            rep["invite_link"] = text
            all_joined = True
            got_peer_id = False

            for sex in niggers:
                try:
                    omega = await sex.join_chat(text)
                    rep["peer_id"] = omega.id
                    got_peer_id = True
                except Exception as e:
                    if "USER_ALREADY_PARTICIPANT" in str(e):
                        try:
                            omega = await sex.get_chat(text)
                            rep["peer_id"] = omega.id
                            got_peer_id = True
                        except Exception as ine:
                            await message.reply(f"⚠️ Error getting chat after already joined: {ine}")
                        continue
                    else:
                        all_joined = False
                        await message.reply(f"⚠️ Error joining chat: {e}")
                        continue

            if got_peer_id:
                rep["step"] = "awaiting_comment"
                await message.reply(
                    "Choose report reason:",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("Child abuse", callback_data="report:final:2"),
                            InlineKeyboardButton("Violence", callback_data="report:final:3")
                        ],
                        [
                            InlineKeyboardButton("Illegal goods", callback_data="report:reason:Goods"),
                            InlineKeyboardButton("Illegal content", callback_data="report:reason:Content")
                        ],
                        [
                            InlineKeyboardButton("Personal data", callback_data="report:reason:Personal"),
                            InlineKeyboardButton("Terrorism", callback_data="report:final:7")
                        ],
                        [
                            InlineKeyboardButton("Scam or spam", callback_data="report:reason:Scam"),
                            InlineKeyboardButton("Copyright", callback_data="report:final:9")
                        ],
                        [
                            InlineKeyboardButton("I don’t like it", callback_data="report:final:1")
                        ]
                    ])
                )
            else:
                rep["step"] = "awaiting_chat_username"
                await message.reply("❌ Could not resolve Peer ID. Please resend the chat username.")


        if step == "awaiting_comment":
            rep["comment"] = text
            rep["step"] = "confirming"
            await message.reply(
                "Are you ready to start reporting?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Yes", callback_data="confirm_yes"),
                     InlineKeyboardButton("No",  callback_data="confirm_no")]
                ])
            )
            return

    if user_id not in user_data:
        return

    user = user_data[user_id]

    if user.get("step") == "awaiting_cookies":
        user["stel_dt"] = text
        user["step"] = "awaiting_ssid"
        await message.reply("Now send your `stel_ssid` cookie value.")

    elif user.get("step") == "awaiting_ssid":
        user["stel_ssid"] = text
        user["step"] = "awaiting_hash"
        await message.reply("Now send your `hash_id`. It looks like: `1097b99d3f9b38e4ca`")

    elif user.get("step") == "awaiting_hash":
        user["hash_id"] = text
        user["step"] = "ready"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Start", callback_data=f"start_{user_id}"),
                InlineKeyboardButton("Cancel", callback_data=f"no_{user_id}")
            ]
        ])
        await message.reply("Ready to start?", reply_markup=keyboard)

def get_submenu_buttons(category, items: dict):
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"report:final:{code}")]
        for name, code in items.items()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="report:back")])
    return InlineKeyboardMarkup(buttons)


@app.on_message(filters.command("report") & filters.user([6586350542, 7863944222]))
async def report_handler(client, message):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Peer", callback_data="report_peer")
        ]
    ])

    await message.reply("Choose what you'd like to report:", reply_markup=buttons)

@app.on_message(filters.command("cancel") & filters.user([6586350542, 7863944222]))
async def cancel_handler(client, message):
    user_id = message.from_user.id
    if user_id in reports:
        del reports[user_id]
        await message.reply("✅ Report process cancelled.")
    else:
        await message.reply("❌ No active report to cancel.")

@app.on_callback_query(filters.regex("cancel_report"))
async def cancel_callback(_, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id in reports:
        del reports[user_id]
        await query.message.edit_text("✅ Report process cancelled.")
    else:
        await query.message.edit_text("❌ No active report to cancel.")


@app.on_callback_query(filters.regex("report_peer"))
async def report_type_callback(_, query: CallbackQuery):
    user_id = query.from_user.id
    rtype = query.data.split("_")[1]
    reports[user_id] = {"step": f"{rtype}_amount", "type": rtype}
    await query.message.edit_text("How many reports do you want to send? (0-5000)")

@app.on_callback_query(filters.regex("^target_(channel|group)$"))
async def target_type_callback(_, query: CallbackQuery):
    user_id = query.from_user.id
    target = query.data.split("_")[1]
    reports[user_id]["target"] = target
    reports[user_id]["step"] = "target_privacy"
    await query.message.edit_text("Is the target public or private?", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Public", callback_data="privacy_public"),
            InlineKeyboardButton("Private", callback_data="privacy_private")]
    ]))

@app.on_callback_query(filters.regex("^privacy_(public|private)$"))
async def privacy_type_callback(_, query: CallbackQuery):
    user_id = query.from_user.id
    privacy = query.data.split("_")[1]
    reports[user_id]["privacy"] = privacy
    if privacy == "private":
        reports[user_id]["step"] = "awaiting_invite_link"
        await query.message.edit_text("Send the private invite link to join the group/channel. Must starts with https://t.me/")
    else:
        reports[user_id]["step"] = "awaiting_chat_username"
        await query.message.edit_text("Send the Chat Username of the public group/channel.")

@app.on_callback_query(filters.regex(r"^report:(reason|final|back):?(.+)?$"))
async def handle_report_reason(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    parts = data.split(":", 2)
    action = parts[1]
    value = parts[2] if len(parts) > 2 else None

    if action == "back":
        await query.message.edit_text(
            "Choose the reason for reporting:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Child abuse", callback_data="report:final:2"),
                    InlineKeyboardButton("Violence", callback_data="report:final:3")
                ],
                [
                    InlineKeyboardButton("Illegal goods", callback_data="report:reason:Goods"),
                    InlineKeyboardButton("Illegal content", callback_data="report:reason:Content")
                ],
                [
                    InlineKeyboardButton("Personal data", callback_data="report:reason:Personal"),
                    InlineKeyboardButton("Terrorism", callback_data="report:final:7")
                ],
                [
                    InlineKeyboardButton("Scam or spam", callback_data="report:reason:Scam"),
                    InlineKeyboardButton("Copyright", callback_data="report:final:9")
                ],
                [
                    InlineKeyboardButton("I don’t like it", callback_data="report:final:1")
                ]
            ])
        )
        return

    if action == "reason":
        category = value
        sub = REASON_CODES.get(category)

        if isinstance(sub, dict):
            await query.message.edit_text(
                f"Select a more specific reason under '{category}':",
                reply_markup=get_submenu_buttons(category, sub)
            )
        else:
            reports[user_id]["reason"] = sub
            reports[user_id]["step"] = "awaiting_comment"
            await query.message.edit_text("Enter a comment/message to go with the report.")
        return

    if action == "final":
        reason_id = int(value)
        reports[user_id]["reason"] = reason_id
        reports[user_id]["step"] = "awaiting_comment"
        await query.message.edit_text("Enter a comment/message to go with the report.")


@app.on_callback_query(filters.regex("^confirm_(yes|no)$"))
async def confirm_callback(_, query: CallbackQuery):
    user_id = query.from_user.id
    confirm = query.data.split("_")[1]

    if confirm == "yes":
        report_data = reports.get(user_id)
        if not report_data:
            await query.message.edit_text("❌ No report data found.")
            return

        report_data["amount"] = report_data.get("amount")

        await query.message.edit_text("🚀 Report starting... tracking progress.")
        reporter = Reporter(app, user_id, report_data, query.message)
        asyncio.create_task(reporter.run())
    else:
        await query.message.edit_text("❌ Report canceled.")
        reports.pop(user_id, None)



@app.on_message(filters.document & ~filters.command(['e', 'sh', 'start', 'cancel', 'report']))
async def handle_file(client, message: Message):
    if message.document.mime_type == "text/plain":
        user_id = message.from_user.id
        path = f"/root/{user_id}_usernames.txt"
        file = await message.download(file_name=path)

        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                usernames = [x.strip().lstrip("@") for x in f if x.strip()]
        except Exception as e:
            os.remove(file)
            return await message.reply(f"Error reading file: {e}")

        if len(usernames) > 50000:
            os.remove(file)
            return await message.reply("You can only scan up to 50000 usernames.")

        user_data[user_id] = {"step": "file_uploaded", "usernames_file": path}
        await message.reply("Got your username list. Now reply with /check on this message to proceed.")


@app.on_message(filters.command("check"))
async def check_command(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or user_data[user_id].get("step") != "file_uploaded":
        await message.reply("You need to upload a username file first.")
        return
    user_data[user_id]["step"] = "awaiting_cookies"
    await message.reply("Please send your `stel_dt` cookie value.")

async def paginate_catog(client, callback, page):
    buttons = chunk_buttons(catogs, page)
    await callback.message.edit("Choose a category:", reply_markup=InlineKeyboardMarkup(buttons))

async def show_videos(client, callback, prefix):
    print('show video clicked', prefix)
    if prefix not in catog_map:
        return await callback.answer("Unknown category", show_alert=True)

    filtered = [v for v in videos if v["catog"] == prefix]
    await send_video_page(callback.message, filtered, prefix)

async def process_video(client, callback, prefix, index):
    filtered = [v for v in videos if v["catog"] == prefix]
    video = filtered[int(index)]
    user_id = callback.from_user.id
    orig_path = video["path"]
    out_path = f"{MUTATED_DIR}/{uuid4().hex}.mp4"
    progress[user_id] = {"done": False, "path": out_path}

    async def mutate_and_set():
        mutator = VideoMutator(orig_path, out_path)
        mutator.mutate()
        progress[user_id]["done"] = True

    asyncio.create_task(mutate_and_set())
    await callback.message.reply("Creating your video...", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Send now", callback_data="send_now")]
    ]))

async def paginate_videos(client, callback, prefix, page):
    page = int(page)
    filtered = [v for v in videos if v["catog"] == prefix]
    await send_video_page(callback.message, filtered, prefix, page)

async def send_final_video(client, callback):
    user_id = callback.from_user.id
    if user_id not in progress:
        return await callback.answer("Nothing pending.", show_alert=True)
    if not progress[user_id]["done"]:
        return await callback.answer("Still processing. Try again.", show_alert=False)

    path = progress[user_id]["path"]
    await callback.message.delete()
    sent = await callback.message.reply_video(video=path, supports_streaming=True, protect_content=True)

    await asyncio.sleep(300)
    try:
        await sent.delete()
    except:
        pass
    os.remove(path)
    del progress[user_id]

@app.on_callback_query()
async def handle_buttons(client, callback):
    data = callback.data
    user_id = callback.from_user.id

    if data.startswith("catog_"):
        prefix = data.split("_", 1)[1]
        print('show video detected', prefix)
        return await show_videos(client, callback, prefix)

    if data.startswith("nav_cat_"):
        page = int(data.split("_")[-1])
        return await paginate_catog(client, callback, page)

    if data.startswith("nav_vid_"):
        prefix, page = data.split("_")[2:]
        return await paginate_videos(client, callback, prefix, page)

    if data.startswith("video_"):
        parts = data.split("_")
        prefix = "_".join(parts[1:-1])
        index = parts[-1]
        return await process_video(client, callback, prefix, index)

    if data == "send_now":
        return await send_final_video(client, callback)

    if data == f"no_{user_id}":
        user_data.pop(user_id, None)
        await callback.message.edit("Process cancelled.")
        return

    if data == f"start_{user_id}":
        user = user_data[user_id]
        with open(user["usernames_file"], "r") as f:
            usernames = [line.strip() for line in f if line.strip()]

        total = len(usernames)
        stel_dt = user["stel_dt"]
        stel_ssid = user["stel_ssid"]
        hash_id = user["hash_id"]

        cookies = {"stel_dt": stel_dt, "stel_ssid": stel_ssid}
        headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded"}

        batches = [usernames] if total <= 50 else [usernames[i:i + max(1, total // 10)] for i in range(0, total, max(1, total // 10))]

        for batch_num, batch in enumerate(batches, 1):
            unavailable, failed, success, claimable = [], [], [], []
            progress_msg = await callback.message.reply(f"Batch {batch_num}/{len(batches)}: {len(batch)} usernames loaded\nHash ID: {hash_id}\nProgress: ░░░░░░░░░░░░░░░░░░░░░░")
            last_bar = ""

            for idx, query in enumerate(batch):
                async with aiohttp.ClientSession(cookies=cookies) as session:
                    try:
                        data = {"type": "usernames", "sort": "", "filter": "", "query": query, "method": "searchAuctions"}
                        url = f"https://fragment.com/api?hash={hash_id}"
                        async with session.post(url, headers=headers, data=data) as resp:
                            if resp.status != 200:
                                failed.append(query)
                                continue
                            json_data = await resp.json()
                            html = json_data.get("html", "")
                            soup = BeautifulSoup(html, "html.parser")

                            block = soup.select_one(".tm-value")
                            status = soup.select_one(".tm-status-avail, .tm-status-taken, .tm-status-unavail")

                            if not block or not status:
                                failed.append(query)
                                continue

                            status_text = status.text.strip().lower()
                            if "unavailable" in status_text:
                                success.append(query)
                            else:
                                failed.append(f"{query} : Already Taken")

                    except Exception as e:
                        failed.append(f"{query} : {str(e)}")

                bar = progress_bar(idx + 1, len(batch))
                if bar != last_bar:
                    try:
                        await progress_msg.edit(f"Batch {batch_num}/{len(batches)}: {len(batch)} usernames loaded\nHash ID: {hash_id}\nProgress: {bar}")
                        last_bar = bar
                    except: pass
                await asyncio.sleep(1)

            for name in success:
                try:
                    res = await mirza.invoke(AccountCheckUsername(username=name))
                    if res:
                        claimable.append(f"{name} : Working")
                    else:
                        failed.append(f"{name} : Exists")
                except UsernameInvalid:
                    failed.append(f"{name} : Banned")
                except Exception as e:
                    err = type(e).__name__
                    failed.append(f"{name} : Unknown error ({err})")

            success_path = f"/root/success_{user_id}_batch{batch_num}.txt"
            failed_path = f"/root/failed_{user_id}_batch{batch_num}.txt"

            if claimable:
                with open(success_path, "w") as s:
                    s.write("\n".join(claimable))
                if os.path.exists(success_path):
                    await callback.message.reply_document(success_path, caption=f"✅ Claimable Usernames (Batch {batch_num})")
                    os.remove(success_path)
            else:
                await callback.message.reply(f"✅ No claimable usernames found in batch {batch_num}.")

            if failed:
                with open(failed_path, "w") as f:
                    f.write("\n".join(failed))
                if os.path.exists(failed_path):
                    await callback.message.reply_document(failed_path, caption=f"❌ Failed Usernames (Batch {batch_num})")
                    os.remove(failed_path)
            else:
                await callback.message.reply(f"All usernames processed in batch {batch_num} — no errors.")

            if batch_num < len(batches):
                await callback.message.reply("⏳ Waiting 1 minute before next batch...")
                await asyncio.sleep(60)

        if os.path.exists(user["usernames_file"]):
            os.remove(user["usernames_file"])
        if user_id in user_data:
            del user_data[user_id]
