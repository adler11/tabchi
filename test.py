import os
import re
from pyrogram import Client, filters
from pytube import YouTube
from pytube.exceptions import RegexMatchError
import urllib.error
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


bot_token = '6433280815:AAGoxHQ0-DJST0E3KXHMlvoxcTAGumnxcME'

# Initialize the Pyrogram client
app = Client("youtube_downloader",bot_token=bot_token)

# Function to extract video ID from YouTube link
def extract_video_id(link):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, link)
    if match:
        return match.group(1)
    else:
        return None

# Function to download YouTube video
def download_video(link, quality):
    video_id = extract_video_id(link)
    if video_id:
        try:
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            if quality == 'MP3':
                audio_stream = yt.streams.filter(only_audio=True).first()
                return audio_stream.download(filename=f"{yt.title}.mp3")
            else:
                video_streams = yt.streams.filter(res=quality).all()
                if video_streams:
                    return video_streams[0].download()
                else:
                    print(f"No available streams for quality: {quality}")
                    return None
        except urllib.error.HTTPError as e:
            if e.code == 410:
                print("Video is no longer available.")
            else:
                print(f"HTTP Error {e.code}: {e.reason}")
            return None
        except RegexMatchError:
            return None
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None
    else:
        return None

# Modify the global scope to store user links
user_links = {}

# Define custom sorting order for qualities
QUALITY_ORDER = {
    "144p": 1,
    "240p": 2,
    "360p": 3,
    "480p": 4,
    "720p": 5,
    "1080p": 6,
    "1440p": 7,
    "2160p": 8,
    "MP3": 9,  # MP3 should be last
}

# Start command handler
@app.on_message(filters.command("start"))
async def start_command(client, message):
  user_first_name = message.from_user.first_name
  await message.reply_text(f"Hello {user_first_name} 👋\n\nSend me a link from YouTube and I will download a video or audio!")

# Message handler
@app.on_message(filters.text & ~filters.command("start"))
async def handle_message(client, message):
    text = message.text

    if 'youtube.com/watch' in text or 'youtu.be' in text:
        await message.reply_text("Please wait while I process the request...")
        # Store the YouTube link
        user_links[message.from_user.id] = text
        # Generate quality keyboard and cover image URL
        result = await generate_quality_keyboard(text)
        if result:
            cover_url, quality_keyboard = result
            # Send the cover image along with the message
            await message.reply_photo(cover_url, caption="🎞 Choose video format", reply_markup=quality_keyboard)
        else:
            await message.reply_text("No video found.")
    else:
        await message.reply_text("Please provide a valid YouTube link.")



# Callback query handler
@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    quality = callback_query.data

    # Retrieve the YouTube link based on the user ID
    link = user_links.get(callback_query.from_user.id)

    if link:
        # Download the video
        filename = download_video(link, quality)

        if filename:
            await callback_query.message.reply_text('Video downloaded successfully! Sending the file...')
            await client.send_document(callback_query.from_user.id, filename)
            # Delete the downloaded file
            os.remove(filename)
        else:
            await callback_query.message.reply_text('Failed to download the video.')
    else:
        await callback_query.message.reply_text('No YouTube link found for this user.')

# Function to generate the quality keyboard dynamically
async def generate_quality_keyboard(link):
    video_id = extract_video_id(link)
    if video_id:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        
        # Get the cover image URL
        cover_url = yt.thumbnail_url
        
        available_qualities = set([stream.resolution for stream in yt.streams.filter(type="video")])
        sorted_qualities = sorted(available_qualities, key=lambda x: QUALITY_ORDER.get(x, float('inf')))
        buttons = []
        for quality in sorted_qualities:
            buttons.append([InlineKeyboardButton(quality, callback_data=quality)])
        
        # Check if MP3 stream is available
        mp3_available = any("audio" in stream.mime_type for stream in yt.streams.filter(only_audio=True))
        if mp3_available:
            buttons.append([InlineKeyboardButton("MP3", callback_data="MP3")])
        
        # Create InlineKeyboardMarkup with quality buttons
        keyboard = InlineKeyboardMarkup(buttons)
        
        return cover_url, keyboard
    else:
        return None



# Run the client
app.run()
