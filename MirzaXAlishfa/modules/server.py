from flask import Flask, send_from_directory, render_template
from flask_socketio import join_room, leave_room
from flask import request
from flask_socketio import SocketIO, emit
from MirzaXAlishfa.modules.song import YTHM
from pyrogram import filters
from pyrogram.types import Message
from flask_socketio import disconnect
from MirzaXAlishfa import app as bot
import threading
import time
from urllib.parse import unquote
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

youtube = YTHM(output_dir="downloads")

ROOMS = {}
USERS = {}
socket_user_map = {}

app = Flask(__name__, static_url_path='', static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*")

@bot.on_message(filters.command('play'))
async def handle_play_command(_, message: Message):
    chat_id = message.chat.id
    query = message.text[6:].strip()
    songid = youtube._search(query)
    path = youtube._mp3(songid)
    info = youtube._details(songid)

    song = {
        'type': 'audio',
        'path': path,
        'title': info['title'],
        'author': info['channel'],
        'thumb': info['thumbnail_url'],
        'duration': info['length_sec']
    }

    ROOMS.setdefault(chat_id, {"queue": [], "current": None})
    room = ROOMS[chat_id]
    if room['current']:
        room['queue'].append(song)
        await message.reply_text(chat_id, f"✅ Queued: {song['title']}")
    else:
        room['current'] = song
        socketio.emit('start_stream', {
            'stream_url': path,
            'title': song['title'],
            'author': song['author'],
            'thumb': song['thumb'],
            'chat_id': chat_id
        }, room=str(chat_id))
        webapp_url = f"https://t.me/{bot.me.username}?startapp={message.chat.id}"
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    text="tst",
                    url=webapp_url
                )]
            ]
        )
        await message.reply_text(chat_id, f"▶️ Now playing: {song['title']}", reply_markup=keyboard)

@bot.on_message(filters.command('vplay'))
async def handle_vplay_command(_, message: Message):
    chat_id = message.chat.id
    query = message.text[6:].strip()
    songid = youtube._search(query)
    path = youtube._mp4(songid)
    info = youtube._details(songid)

    song = {
        'type': 'video',
        'path': path,
        'title': info['title'],
        'author': info['channel'],
        'duration': info['length_sec'],
        'thumb': info['thumbnail_url']
    }

    ROOMS.setdefault(chat_id, {"queue": [], "current": None})
    room = ROOMS[chat_id]
    if room['current']:
        room['queue'].append(song)
        message.reply_text(chat_id, f"✅ Queued: {song['title']}")
    else:
        room['current'] = song
        socketio.emit('start_stream', {
            'stream_url': path,
            'title': song['title'],
            'author': song['author'],
            'thumb': song['thumb'],
            'chat_id': chat_id
        }, room=str(chat_id))
        webapp_url = f"https://t.me/{bot.me.username}?startapp={message.chat.id}"
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    text="tst",
                    url=webapp_url
                )]
            ]
        )
        await message.reply_text(chat_id, f"▶️ Now playing: {song['title']}", reply_markup=keyboard)

@bot.on_message(filters.command('skip'))
async def skip_track(_, message: Message):
    parts = message.text.split()
    chat_id = message.chat.id
    skip_count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    room = ROOMS[chat_id]
    for _ in range(skip_count):
        if room['queue']:
            room['current'] = room['queue'].pop(0)
        else:
            room['current'] = None
            break

    if room['current']:
        song = room['current']
        socketio.emit('start_stream', {
            'stream_url': song['path'],
            'title': song['title'],
            'author': song['author'],
            'thumb': song['thumb'],
            'chat_id': chat_id
        }, room=str(chat_id))
        webapp_url = f"https://t.me/{bot.me.username}?startapp={message.chat.id}"
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    text="tst",
                    url=webapp_url
                )]
            ]
        )
        await message.reply_text(chat_id, f"▶️ Now playing: {song['title']}", reply_markup=keyboard)
    else:
        socketio.emit('stop_stream', {}, room=str(chat_id))
        await message.reply_text(chat_id, "🚫 Queue is empty, nothing to play.")

@bot.on_message(filters.command('queue'))
async def queuecmd(_, message: Message):
    queue = ROOMS[message.chat.id]['queue']
    response = "\n".join([f"#{i+1} - {track['title']}" for i, track in enumerate(queue)]) or "Queue is empty."
    await message.reply_text(response)

@bot.on_message(filters.command('stop'))
async def stopcmd(_, message: Message):
    chat_id = str(message.chat.id)
    ROOMS[chat_id] = {'queue': [], 'current': None}
    socketio.emit('stop_stream', {'id': chat_id})
    await message.reply_text("⛔ Stopped all songs and cleared the queue.")


@app.route('/chat')
def index():
    return send_from_directory(directory='.', path='index.html')

@app.route('/downloads/<path:filename>')
def serve_music(filename):
    filename = unquote(filename)
    return send_from_directory('/home/ubuntu/devbot/alishfa/MirzaXAlishfa/modules/downloads', filename)

@socketio.on('stop_stream')
def handle_stop_stream(data):
    chat_id = data.get('id')
    print(f"⛔ Stop signal received for chat: {chat_id}")
    emit('stop_stream', {}, room=str(chat_id))

@socketio.on('user_joined')
def handle_user_joined(user):
    chat_id = str(user.get('chatId'))
    user_id = user.get('id')
    socket_user_map[request.sid] = (chat_id, user_id)

    join_room(chat_id)

    if chat_id not in USERS:
        USERS[chat_id] = {}

    USERS[chat_id][user_id] = user

    print(f"[+] {user['first_name']} joined VC in chat {chat_id}")

    emit('participant_list', list(USERS[chat_id].values()), to=request.sid)

    emit('new_participant', user, room=chat_id, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f'[-] Disconnected SID: {sid}')
    if sid in socket_user_map:
        chat_id, user_id = socket_user_map.pop(sid)
        leave_room(chat_id)
        if chat_id in USERS:
            user = USERS[chat_id].pop(user_id, None)
            if user:
                printo(f"[-] User left: {user}")
                emit('participant_left', user, room=chat_id, include_self=False)

@socketio.on('connect')
def on_connect():
    print('Client connected')
    emit('connected', {'status': 'OK'}, broadcast=False)

@socketio.on('play_song')
def handle_play_song(data):
    chat_id = data.get('id')
    songname = data.get("songname")

    if not chat_id:
        emit('start_stream', {'error': 'Invalid or missing chat ID'})
        return

    if not songname:
        emit('start_stream', {'error': 'No song name provided'})
        return

    print(f"🎵 Request to stream: {songname}")
    songid = youtube._search(songname)
    path = youtube._mp3(songid)
    info = youtube._details(songid)

    start_time = time.time()

    ROOMS.setdefault(chat_id, {"queue": []})
    ROOMS[chat_id]['current'] = {
        'type': 'audio',
        'path': path,
        'title': songname,
        "author": info["channel"],
        "start_time": start_time
    }

    emit('start_stream', {
        'stream_url': path,
        'title': info.get('title', 'Unknown Title'),
        'author': info.get('channel', 'Unknown Artist'),
        'thumb': info.get('thumbnail_url', '')
    }, room=chat_id, broadcast=True)


@socketio.on('pause_song')
def handle_pause_song():
    print("⏸️ Pause requested")
    emit('pause_all', broadcast=True)

@socketio.on('resume_song')
def handle_resume_song():
    print("▶️ Resume requested")
    emit('resume_all', broadcast=True)

@socketio.on('seek_song')
def handle_seek_song(data):
    time = data.get('time')
    print(f"⏩ Seek to {time:.2f}s requested")
    emit('seek_all', {'time': time}, broadcast=True)

@socketio.on('play_video')
def handle_play_video(data):
    videoname = data.get("videoname")
    chat_id = data.get('id')
    if not videoname:
        emit('start_video_stream', {'error': 'No filename provided'})
        return

    print(f"🎬 Request to stream video: {videoname}")
    songid = youtube._search(videoname)
    path = youtube._mp4(songid)
    info = youtube._details(songid)
    print(info)
    ROOMS[chat_id]['current'] = {'type': 'audio', 'path': path, 'title': videoname}
    print(ROOMS)
    emit('start_video_stream', {
        'stream_url': path, 
        'title': info.get('title', 'Unknown Title'),
        'author': info.get('channel', 'Unknown Artist'),
    }, broadcast=True)

@socketio.on('pause_video')
def handle_pause_video():
    emit('pause_video', broadcast=True)

@socketio.on('resume_video')
def handle_resume_video():
    emit('resume_video', broadcast=True)

@socketio.on('seek_video')
def handle_seek_video(data):
    time = data.get("time")
    emit('seek_video', {'time': time}, broadcast=True)


@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

def run_socket():
    print("🔌 Starting socket server on port 5000...")
    socketio.run(app, host="0.0.0.0", port=5000)


threading.Thread(target=run_socket, daemon=True).start()