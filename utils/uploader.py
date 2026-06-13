import os
import time
from pyrogram import Client
from pyrogram.types import Message
from utils.progress import progress_for_pyrogram

async def upload_video(client: Client, file_path: str, message: Message, chat_id: int):
    """
    Uploads the downloaded video to Telegram.
    """
    start_time = time.time()
    
    try:
        await message.edit_text("📤 **Uploading to Telegram...**")
        
        await client.send_video(
            chat_id=chat_id,
            video=file_path,
            caption="**Downloaded via Leach Bot**",
            supports_streaming=True,
            progress=progress_for_pyrogram,
            progress_args=("📤 **Uploading...**", message, start_time)
        )
        
        await message.delete()
    except Exception as e:
        await message.edit_text(f"❌ **Upload Failed:** {str(e)}")
    finally:
        # Clean up the file after uploading
        if os.path.exists(file_path):
            os.remove(file_path)
