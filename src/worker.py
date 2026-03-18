import os
import json
import asyncio
import time
from pyrogram import Client

async def main():
    # 1. Load payload from TBC
    payload_str = os.environ.get("PAYLOAD", "{}")
    payload = json.loads(payload_str)
    
    msg_id = int(payload.get("msg_id", 0))
    new_name = payload.get("new_name")
    thumb_msg_id = int(payload.get("thumb_msg_id", 0))
    chat_id = int(payload.get("chat_id", 0))
    bot_token = payload.get("bot_token")
    
    # 2. Load API Credentials from GitHub Secrets
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")

    if not all([msg_id, new_name, chat_id, API_ID, API_HASH, bot_token]):
        print("Missing required parameters or secrets.")
        return

    # 3. Initialize Pyrogram Client (Logged in as BOT)
    # This allows native 2GB MTProto downloads/uploads without a user session!
    app = Client(
        "renamer_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=bot_token
    )

    async with app:
        try:
            # Notify user
            status_msg = await app.send_message(chat_id, "📥 **Downloading 2GB file to backend...**")
            
            # --- DOWNLOAD MAIN FILE ---
            file_message = await app.get_messages(chat_id, msg_id)
            
            # Download file & rename it directly on the disk
            file_path = await app.download_media(file_message, file_name=new_name)
            
            # --- DOWNLOAD THUMBNAIL (If exists) ---
            thumb_path = None
            if thumb_msg_id > 0:
                await app.edit_message_text(chat_id, status_msg.id, "🖼️ **Processing thumbnail...**")
                thumb_message = await app.get_messages(chat_id, thumb_msg_id)
                thumb_path = await app.download_media(thumb_message, file_name="thumb.jpg")

            # --- UPLOAD PROCESSED FILE ---
           # --- UPLOAD PROCESSED FILE ---
            await app.edit_message_text(chat_id, status_msg.id, "📤 **Uploading renamed file...**")
            
            upload_type = payload.get("upload_type", "type_video")
            
            if upload_type == "type_video":
                await app.send_video(
                    chat_id=chat_id,
                    video=file_path,
                    thumb=thumb_path,
                    file_name=new_name,
                    caption=f"✅ **Renamed:** `{new_name}`"
                )
            else:
                await app.send_document(
                    chat_id=chat_id,
                    document=file_path,
                    thumb=thumb_path,
                    file_name=new_name,
                    caption=f"✅ **Renamed:** `{new_name}`"
                )
            
            await app.edit_message_text(chat_id, status_msg.id, "🎉 **Process Complete!**")

        except Exception as e:
            await app.send_message(chat_id, f"❌ **Backend Engine Error:** {str(e)}")
            
        finally:
            # --- CLEANUP DISK (Free up GitHub Runner Space) ---
            if 'file_path' in locals() and file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)

if __name__ == "__main__":
    asyncio.run(main())
