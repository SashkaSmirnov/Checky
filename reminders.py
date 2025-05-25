from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from telegram import Bot
import asyncio

# create and start the background scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# schedule a reminder one hour before the task deasline
def schedule_reminder(bot_token, chat_id, message, due_datetime):
    bot = Bot(token=bot_token)
    reminder_time = due_datetime - timedelta(hours=1)

    # async message sender
    async def send_async():
        await bot.send_message(chat_id=chat_id, text=message)

    def run_async_job():
        asyncio.run(send_async())

    # schedule only if reminder time is in the future
    if reminder_time > datetime.now():
        scheduler.add_job(
            run_async_job,
            trigger='date',
            run_date=reminder_time
        )
        print(f"✅ Reminder scheduled for {reminder_time}")
    else:
        print(f"⚠️ Reminder time {reminder_time} is in the past. Not scheduling.")

# notification for deadline
def schedule_deadline_passed_reminder(bot_token, chat_id, task_title, due_datetime):
    bot = Bot(token=bot_token)

    async def send_deadline_notice():
        await bot.send_message(chat_id=chat_id, text=f"⏰ The deadline for '{task_title}' has passed!")

    def run_deadline_job():
        asyncio.run(send_deadline_notice())

    if due_datetime > datetime.now():
        scheduler.add_job(
            run_deadline_job,
            trigger='date',
            run_date=due_datetime
        )
        print(f"📌 Deadline notice scheduled for {due_datetime}")
    else:
        print(f"⚠️ Deadline {due_datetime} is in the past. Not scheduling missed-deadline notice.")