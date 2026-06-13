from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import AUTH_USERS

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    # if message.from_user.id not in AUTH_USERS:
    #     await message.reply_text("❌ You are not authorized to use this bot.")
    #     return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Login & Extract", callback_data="menu_platforms")],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"),
            InlineKeyboardButton("❓ Help", callback_data="menu_help")
        ]
    ])
    
    banner_path = "assets/bot_banner.png"
    caption = (
        "**⚡ WELCOME TO CLEAN LEACH ENGINE ⚡**\n\n"
        "> _Your ultimate automated extraction and uploading suite._\n\n"
        "💠 **Status:** `Online & Ready`\n"
        "💠 **WAF Bypass:** `Active`\n\n"
        "**Select an option below to begin your extraction:**"
    )
    
    import os
    if os.path.exists(banner_path):
        await message.reply_photo(
            photo=banner_path,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await message.reply_text(caption, reply_markup=keyboard)


@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    if message.from_user.id not in AUTH_USERS:
        return
        
    help_text = """
**Available Commands:**
/start - Check if bot is alive
/help - Show this message
/addauth [user_id] - Add an authorized user (Admin only)
/rmauth [user_id] - Remove an authorized user (Admin only)
/users - List authorized users (Admin only)

Send any link to download it!
    """
    await message.reply_text(help_text)
