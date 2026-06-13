import os
import yt_dlp
import asyncio
from pyrogram.types import Message

async def download_video(url: str, output_dir: str, message: Message) -> str:
    """
    Downloads a video using yt-dlp and returns the file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': file_path,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    # Run yt-dlp in a separate thread so it doesn't block the async loop
    def run_ytdlp():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    await message.edit_text("⏳ **Downloading video...**\n(This might take a while depending on file size)")
    loop = asyncio.get_event_loop()
    
    try:
        downloaded_file = await loop.run_in_executor(None, run_ytdlp)
        return downloaded_file
    except Exception as e:
        raise Exception(f"Download Failed: {str(e)}")
