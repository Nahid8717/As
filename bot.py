import os
import datetime
import requests
from pymongo import MongoClient
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# ==== Config (Environment Variables থেকে) ====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
GPLINKS_API = os.getenv("GPLINKS_API")
MONGO_URI = os.getenv("MONGO_URI")

# ==== MongoDB ====
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# ==== Verify Check ====
def is_verified(user_id):
    user = users.find_one({"userId": user_id})
    if not user:
        return False
    last = user.get("lastVerified")
    if not last:
        return False
    return (datetime.datetime.now() - last).total_seconds() < 3 * 60 * 60  # 3 hours

# ==== GPLinks Shortener ====
def shorten_link(url):
    try:
        r = requests.get(f"https://gplinks.in/api?api={GPLINKS_API}&url={url}")
        data = r.json()
        return data.get("shortenedUrl", url)
    except:
        return url

# ==== Commands ====
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 স্বাগতম! ভিডিও দেখতে চাইলে আগে ভেরিফাই করুন /verify")

def verify(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    # Polling system এ callback URL দরকার নাই, ডেমো দেখানোর জন্য শুধু একটা লিংক
    short_link = shorten_link("https://gplinks.in/")
    update.message.reply_text(f"✅ ভেরিফাই করতে এখানে ক্লিক করুন:\n{short_link}")

def video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_verified(user_id):
        update.message.reply_text("⚠️ আগে ভেরিফাই করুন! /verify ব্যবহার করুন।")
        return
    update.message.reply_video(
        "https://file-examples.com/storage/fe5e1a2b3b9/video.mp4",
        caption="🎬 এখানে আপনার ভিডিও"
    )

def delete_videos(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != str(ADMIN_ID):
        return
    users.update_many({}, {"$set": {"lastVerified": None}})
    update.message.reply_text("🗑️ সব ইউজারের ভেরিফাই ডেটা রিসেট করা হয়েছে।")

# ==== Main ====
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("verify", verify))
    dp.add_handler(CommandHandler("video", video))
    dp.add_handler(CommandHandler("deletevideos", delete_videos))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
