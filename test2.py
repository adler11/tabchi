from pyrogram import Client, filters
import instaloader
import os
import shutil

# Pyrogram initialization parameters
api_id = 4634028
api_hash = 'ce8e3cd6539ba91704627d94c3ba44dd'
bot_token = '6433280815:AAGoxHQ0-DJST0E3KXHMlvoxcTAGumnxcME'

# Initialize the Pyrogram client
app = Client("pov", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

L = instaloader.Instaloader()  # Define L globally

# Load or create session
session_file = "instaloader.session"
if os.path.isfile(session_file):
    L.load_session_from_file("adlerdrr", filename=session_file)
else:
    L.context.log("Session file not found. Logging in...")
    L.interactive_login("adlerdrr")  # Replace "adlerdrr" with your Instagram username
    L.save_session_to_file(session_file)

def download_post(post_url):
    try:
        # Create a temporary directory
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Load the post
        post = instaloader.Post.from_shortcode(L.context, post_url.split("/")[-2])

        # Download the post to the temporary directory
        L.download_post(post, target=temp_dir)
        
        # Get list of downloaded media files
        media_files = [filename for filename in os.listdir(temp_dir) if filename.endswith(('jpg', 'mp4'))]

        # Get caption from post
        caption = post.caption if post.caption else "🚫 (no caption)"

        return media_files, caption, temp_dir
    except Exception as e:
        return f"⚠️ Error: {e}", None, None


def download_story(username):
    try:
        # Create a temporary directory
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Get user id
        profile = instaloader.Profile.from_username(L.context, username)
        userid = profile.userid

        # Download the story to the temporary directory
        L.download_stories(userids=[userid], filename_target=temp_dir)
        
        # Get list of downloaded media files
        story_files = [filename for filename in os.listdir(temp_dir) if filename.endswith(('jpg', 'mp4'))]

        return story_files, temp_dir
    except Exception as e:
        return f"⚠️ Error: {e}", None


@app.on_message(filters.command("post"))
def download_instagram_post(_, message):
    try:
        post_url = message.text.split(maxsplit=1)[1]
        if post_url.startswith("https://www.instagram.com/p/") or post_url.startswith("https://instagram.com/p/") or post_url.startswith("https://www.instagram.com/reel/") or post_url.startswith("https://instagram.com/reel/"):
            message.reply_text("📥 Downloading...")
            media_files, caption, temp_dir = download_post(post_url)
            if temp_dir:
                # Sort the media files by filename
                media_files.sort()
                # Get the last file in the sorted list (main post file)
                main_post_file = media_files[-1]
                with open(os.path.join(temp_dir, main_post_file), "rb") as file:
                    message.reply_text("✅ Done, Uploading...")
                    if main_post_file.endswith('.jpg'):
                        message.reply_photo(file, caption=caption)
                    elif main_post_file.endswith('.mp4'):
                        message.reply_video(file, caption=caption)
                # Delete temporary directory
                shutil.rmtree(temp_dir)
        else:
            message.reply_text("❌ Invalid URL. Please provide a valid Instagram post URL.")
    except IndexError:
        message.reply_text("❌ Invalid command format. Use /post link")


@app.on_message(filters.command("s"))
def send_stories(_, message):
    try:
        _, username = message.text.split(maxsplit=1)
        message.reply_text("📥 Downloading Stories...")
        story_files, temp_dir = download_story(username)
        if temp_dir:
            message.reply_text("✅ Done, Uploading Stories...")
            for story_file in story_files:
                with open(os.path.join(temp_dir, story_file), "rb") as file:
                    if story_file.endswith('.jpg'):
                        message.reply_photo(file)
                    elif story_file.endswith('.mp4'):
                        message.reply_video(file)
            # Delete temporary directory
            shutil.rmtree(temp_dir)
    except ValueError:
        message.reply_text("❌ Invalid command format. Use /s username")


@app.on_message(filters.command(["help"]))
def help_command(_, message):
    help_text = """\
    🤖 Welcome to Instagram Downloader Bot!

    Here are the available commands:
    /post <post_url> - Download and send an Instagram post.
    /s <username> - Download and send stories from the specified Instagram user.
    /help - Show this help message.
    /start - Start the bot.
    """
    message.reply_text(help_text)


@app.on_message(filters.command(["start"]))
def start_command(_, message):
    start_text = """\
    🌟 Welcome to Instagram Downloader Bot!

    Send /help to see the list of available commands.
    """
    message.reply_text(start_text)

# Start the bot
app.run()
