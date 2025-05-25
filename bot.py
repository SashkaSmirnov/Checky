from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)
from db import init_db, add_task, get_user_tasks, mark_task_completed, delete_task
from reminders import schedule_reminder, schedule_deadline_passed_reminder
from datetime import datetime, timedelta

# States
CHOOSING, ENTER_TITLE, ENTER_DATE, ENTER_TIME, CHOOSE_TAG, VIEW_TASKS = range(6)

TOKEN = '7371685386:AAH-0_78Y9uutE7lqagj9DceqCFoEUv_Jtc'


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Create Task", callback_data='create')],
        [InlineKeyboardButton("View Tasks", callback_data='view')]
    ]
    await update.message.reply_text("Hi, I'm Checky! What would you like to do?",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'create':
        await query.edit_message_text("What's the title gonna be?")
        return ENTER_TITLE
    elif query.data == 'view':
        await show_task_list(query)
        return VIEW_TASKS
    elif query.data == 'back':
        keyboard = [
            [InlineKeyboardButton("Create Task", callback_data='create')],
            [InlineKeyboardButton("View Tasks", callback_data='view')]
        ]
        await query.edit_message_text(
            text="What would you like to do?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOOSING


async def task_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('task_'):
        task_id = int(query.data.split('_')[1])
        tasks = get_user_tasks(query.from_user.id)
        task = next((t for t in tasks if t[0] == task_id), None)

        if task:
            task_id, title, tag, due_date_str, completed = task
            status = "Completed" if completed else "Incomplete"
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d %H:%M').strftime('%d-%m-%Y %H:%M')

            keyboard = []
            if not completed:
                keyboard.append([InlineKeyboardButton("Mark as Complete", callback_data=f"complete_{task_id}")])
            keyboard.append([
                InlineKeyboardButton("Delete Task", callback_data=f"delete_{task_id}"),
                InlineKeyboardButton("Back to Tasks", callback_data='view')
            ])

            await query.edit_message_text(
                text=f"Task: {title}\nTag: {tag}\nDue: {due_date}\nStatus: {status}\n",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    elif query.data.startswith('complete_'):
        task_id = int(query.data.split('_')[1])
        mark_task_completed(task_id)
        await show_task_list(query)
    elif query.data.startswith('delete_'):
        task_id = int(query.data.split('_')[1])
        delete_task(task_id)
        await query.edit_message_text(text="Task deleted successfully!")
        await show_task_list(query)
    elif query.data == 'view':
        await show_task_list(query)
    elif query.data == 'back':
        keyboard = [
            [InlineKeyboardButton("Create Task", callback_data='create')],
            [InlineKeyboardButton("View Tasks", callback_data='view')]
        ]
        await query.edit_message_text(
            text="What would you like to do?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOOSING

    return VIEW_TASKS


async def show_task_list(query):
    tasks = get_user_tasks(query.from_user.id)
    keyboard = []
    for task in tasks:
        task_id, title, tag, due_date_str, completed = task
        status = "✅" if completed else "❌"
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d %H:%M').strftime('%d-%m-%Y %H:%M')
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {title} | {tag} | Due: {due_date}",
                callback_data=f"task_{task_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton("Back to Menu", callback_data='back')])
    await query.edit_message_text(
        text="Your tasks:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    keyboard = [[InlineKeyboardButton(t, callback_data=t)] for t in ['Home', 'Work', 'Leisure', 'Urgent', 'Other']]
    await update.message.reply_text("Choose a tag!", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_TAG


async def choose_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['tag'] = query.data

    # Create date selection keyboard with DD-MM-YYYY format display
    today = datetime.now().date()
    keyboard = [
        [
            InlineKeyboardButton("Today", callback_data=today.strftime("%d-%m-%Y")),
            InlineKeyboardButton("Tomorrow", callback_data=(today + timedelta(days=1)).strftime("%d-%m-%Y"))
        ],
        [
            InlineKeyboardButton("Custom Date", callback_data="custom_date")
        ]
    ]
    await query.edit_message_text("Select the due date!", reply_markup=InlineKeyboardMarkup(keyboard))
    return ENTER_DATE


async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "custom_date":
        await query.edit_message_text("Enter the date in DD-MM-YYYY format (e.g. 31-12-2023):")
        return ENTER_DATE

    context.user_data['date'] = query.data

    # Create time selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("Morning (9:00)", callback_data="09:00"),
            InlineKeyboardButton("Afternoon (14:00)", callback_data="14:00")
        ],
        [
            InlineKeyboardButton("Evening (19:00)", callback_data="19:00"),
            InlineKeyboardButton("Custom Time", callback_data="custom_time")
        ]
    ]
    await query.edit_message_text("Select time:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ENTER_TIME


async def receive_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Validate date format (DD-MM-YYYY)
        date_str = update.message.text
        datetime.strptime(date_str, "%d-%m-%Y")  # This validates the format
        context.user_data['date'] = date_str

        keyboard = [
            [
                InlineKeyboardButton("Morning (9:00)", callback_data="09:00"),
                InlineKeyboardButton("Afternoon (14:00)", callback_data="14:00")
            ],
            [
                InlineKeyboardButton("Evening (19:00)", callback_data="19:00"),
                InlineKeyboardButton("Custom Time", callback_data="custom_time")
            ]
        ]
        await update.message.reply_text("Select time:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ENTER_TIME
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use DD-MM-YYYY (e.g. 31-12-2023)")
        return ENTER_DATE


async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "custom_time":
        await query.edit_message_text("Enter the time in HH:MM format (e.g. 15:30):")
        return ENTER_TIME

    context.user_data['time'] = query.data

    # Combine date and time (convert from DD-MM-YYYY to YYYY-MM-DD for storage)
    try:
        date_obj = datetime.strptime(context.user_data['date'], "%d-%m-%Y")
        due_date_str = f"{date_obj.strftime('%Y-%m-%d')} {context.user_data['time']}"
        context.user_data['due_date'] = due_date_str
        user_id = query.from_user.id
        title = context.user_data['title']
        tag = context.user_data['tag']
        due_date_str = context.user_data['due_date']
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M")
        add_task(user_id, title, tag, due_date_str, completed=False)
        chat_id = query.message.chat.id
        schedule_reminder(TOKEN, chat_id, f"Reminder: {title}", due_date)
        schedule_deadline_passed_reminder(TOKEN, chat_id, title, due_date)

        keyboard = [
            [InlineKeyboardButton("Create Task", callback_data='create')],
            [InlineKeyboardButton("View Tasks", callback_data='view')]
        ]
        await query.edit_message_text(
            text="Task created and reminder set!\n\nWhat would you like to do next?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOOSING
    except ValueError:
        await query.edit_message_text("Invalid date format. Please start over.")
        return CHOOSING


async def receive_custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Validate time format
        time_str = update.message.text.strip()
        datetime.strptime(time_str, "%H:%M")  # format check
        context.user_data['time'] = time_str

        # Combine with the date
        date_str = context.user_data['date']
        full_datetime_str = f"{date_str} {time_str}"  # e.g. 25-05-2025 15:30
        due_date = datetime.strptime(full_datetime_str, "%d-%m-%Y %H:%M")

        context.user_data['due_date'] = due_date.strftime("%Y-%m-%d %H:%M")  # for DB

        # Save task and schedule reminder
        user_id = update.message.from_user.id
        title = context.user_data['title']
        tag = context.user_data['tag']

        add_task(user_id, title, tag, due_date.strftime("%Y-%m-%d %H:%M"), completed=False)
        chat_id = update.message.chat.id
        schedule_reminder(TOKEN, chat_id, f"Reminder: {title}", due_date)
        schedule_deadline_passed_reminder(TOKEN, chat_id, title, due_date)

        keyboard = [
            [InlineKeyboardButton("Create Task", callback_data='create')],
            [InlineKeyboardButton("View Tasks", callback_data='view')]
        ]
        await update.message.reply_text(
            "Task created and reminder set!\n\nWhat would you like to do next?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOOSING

    except ValueError:
        await update.message.reply_text("Invalid time format. Please use HH:MM (e.g. 15:30)")
        return ENTER_TIME


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [CallbackQueryHandler(menu_handler)],
            ENTER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            CHOOSE_TAG: [CallbackQueryHandler(choose_tag)],
            ENTER_DATE: [
                CallbackQueryHandler(enter_date),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_date)
            ],
            ENTER_TIME: [
                CallbackQueryHandler(enter_time),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_time)
            ],
            VIEW_TASKS: [CallbackQueryHandler(task_detail_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bot is running")
    app.run_polling()


if __name__ == "__main__":
    main()