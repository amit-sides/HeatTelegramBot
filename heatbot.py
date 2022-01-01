#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import json

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

AVAILABLE_COMMANDS = """The available commands are:
/start         - Starts interaction with HeatBot.
/status      - Shows the status of the HeatBot.
/on             - Turns the heat on.
/off             - Turns the heat off."""
LAST_COMMANDS = """
/force_on  - Turns the heat on, regardless of it's current status. Shouldn't be used unless something is wrong...
/force_off - Turns the heat off, regardless of it's current status. Shouldn't be used unless something is wrong...
/help          - Shows this message.
"""
MASTER_COMMANDS = """
/abort        - Aborts the current operation.
/add           - Adds a new user to the HeatBot.
/remove    - Removes a user from the HeatBot.
/list            - Lists all the users."""

# Enable logging
LOG_FILE = "heatbot.log"
"""
IntelliJ Logging format:
Message Pattern: ^\[\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3}\]\s\{\w*\.py:\d*\}\s(\S*)\s*-\s(.*)$
Message Start Pattern: ^\[\d{4}-\d{2}-\d{2}
Time Format: yyyy-MM-dd HH:mm:ss,SSS
Line Highlights:
"^\s*ERROR?\s*$" action="HIGHLIGHT_LINE" fg="-65536" stripe="true"
"^\s*WARN(ING)?\s*$" action="HIGHLIGHT_LINE" fg="-22016" bold="true"
"^\s*INFO\s*$" action="HIGHLIGHT_LINE" fg="-12599489"
"^\s*DEBUG\s*$" action="HIGHLIGHT_LINE" fg="-14927361" stripe="true"
"^\s*CRITICAL\s*$" action="HIGHLIGHT_LINE" fg="-65536" bold="true" italic="true" stripe="true"
"""
FORMATTER = logging.Formatter("[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s")
LOG_HANDLER = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024 * 1024, backupCount=5)
LOG_HANDLER.setFormatter(FORMATTER)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(LOG_HANDLER)

configuration = dict()
ID, ADD, REMOVE_ID = range(3)


def verify_id(func):
    def verifier(update, context):
        user = update.message.from_user
        user_id = str(user["id"])
        if user_id not in configuration["Allowed"]:
            update.message.reply_text(f"You are not allowed to use this bot! Your user id is: {user_id}.")
            logger.warning(f"Unknown user interacting with the bot. User ID: {user_id}.")
            return ConversationHandler.END
        return func(update, context)

    return verifier


def verify_master(func):
    def verifier(update, context):
        user = update.message.from_user
        user_id = str(user["id"])
        if user_id != configuration["MasterID"]:
            update.message.reply_text("You are not allowed to use this command! Only the master shall do that!")
            logger.warning(f"User trying to impersonate Master. User ID: {user_id}.")
            return ConversationHandler.END
        return func(update, context)

    return verifier


def abort(update, context):
    if "name_to_add" in context.user_data:
        del context.user_data["name_to_add"]
    update.message.reply_text("Operation aborted.")
    return ConversationHandler.END


def start(update, context):
    keyboard = [[InlineKeyboardButton("Help 🤷‍♂️", callback_data="/help"), InlineKeyboardButton("Status❔", callback_data="/status")],
                [InlineKeyboardButton("ON 💡", callback_data="/on"), InlineKeyboardButton("OFF 🍗", callback_data="/off")]]
    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Hi! I'm your HeatBot!\nI'm here to help you turn your heater on and off :)", reply_markup=markup)


@verify_id
def help(update, context):
    help_message = AVAILABLE_COMMANDS

    user = update.message.from_user
    user_id = str(user["id"])
    if user_id == configuration["MasterID"]:
        help_message += MASTER_COMMANDS

    help_message += LAST_COMMANDS
    update.message.reply_text(help_message)


@verify_master
def get_name(update, context):
    update.message.reply_text("Please enter the name of the user you want to add.")
    return ID  # Go to get_id


@verify_master
def get_id(update, context):
    name = update.message.text
    context.user_data["name_to_add"] = name
    update.message.reply_text(f"You are about to add '{name}'. Please enter their User ID. For example: '123456789'.")
    return ADD  # Go to add_user


@verify_master
def add_user(update, context):
    global configuration

    user_id = update.message.text
    if user_id == "/abort":
        return abort(update, context)

    if not user_id.isdecimal():
        update.message.reply_text(f"The User ID is invalid! It must contain numbers only! received: '{user_id}'.")
        update.message.reply_text(f"Please try again, or send /abort to abort operation.")
        return ADD

    configuration["Allowed"][user_id] = context.user_data["name_to_add"]
    save_configuration()
    logger.info(f"Added new user: {configuration['Allowed'][user_id]} - {user_id}")
    if "name_to_add" in context.user_data:
        del context.user_data["name_to_add"]
    update.message.reply_text(f"User {configuration['Allowed'][user_id]} was added successfully!")
    return ConversationHandler.END  # Go the add_user


@verify_master
def remove_id(update, context):
    update.message.reply_text("Please enter the User ID of the user you want to remove. For example: '123456789'.")
    return REMOVE_ID  # Go to remove


@verify_master
def remove(update, context):
    global configuration

    user_id = update.message.text
    if user_id == "/abort":
        return abort(update, context)

    if not user_id.isdecimal():
        update.message.reply_text(f"The User ID is invalid! It must contain numbers only! received: '{user_id}'.")
        update.message.reply_text(f"Please try again, or send /abort to abort operation.")
        return REMOVE_ID

    if user_id not in configuration["Allowed"]:
        update.message.reply_text(f"The User ID '{user_id}' was not found in the allowed list.")
        update.message.reply_text(f"Please try again, or send /abort to abort operation.")
        return REMOVE_ID

    name = configuration["Allowed"][user_id]
    del configuration["Allowed"][user_id]
    save_configuration()
    logger.info(f"Removed user: {name} - {user_id}")
    update.message.reply_text(f"User '{name}' was removed successfully!")
    return ConversationHandler.END


@verify_id
def list_users(update, context):
    global configuration

    message = "The following users are allowed to use this bot:"
    if len(configuration["Allowed"]) <= 0:
        message += "\nNo users found."
    else:
        for user_id, user_name in configuration["Allowed"].items():
            message += "\n%20s - %s" % (user_name, user_id)
    update.message.reply_text(message)
    return ConversationHandler.END


def get_status():
    global configuration

    last_change = datetime.datetime.fromtimestamp(configuration["LastChange"])
    last_change_duration = datetime.datetime.now() - last_change
    hours = last_change_duration.seconds // 3600 + last_change_duration.days * 24
    minutes = (last_change_duration.seconds // 60) % 60

    duration_string = ""
    if hours > 1:
        duration_string += f"{hours} hours and "
    elif hours == 1:
        duration_string += f"{hours} hour and "
    duration_string += f"{minutes} minutes"

    if configuration["CurrentStatus"] == "ON":
        status = f"The heat has been ON for {duration_string}."
    elif configuration["CurrentStatus"] == "OFF":
        status = f"The heat has been OFF for {duration_string}."
    else:
        status = f"Current Status: UNKNOWN.\nLast status change: {duration_string} ago."
    return status


@verify_id
def status(update, context):
    update.message.reply_text(get_status())
    return ConversationHandler.END

def turn_on():
    configuration["CurrentStatus"] = "ON"
    configuration["LastChange"] = datetime.datetime.now().timestamp()
    save_configuration()
    return True

def turn_off():
    configuration["CurrentStatus"] = "OFF"
    configuration["LastChange"] = datetime.datetime.now().timestamp()
    save_configuration()
    return True

@verify_id
def on(update, context):
    global configuration

    if configuration["CurrentStatus"] == "ON":
        return status(update, context)

    update.message.reply_text("Should turn bot ON here...")
    if turn_on():
        update.message.reply_text("Turned Heatbot ON.")
    else:
        update.message.reply_text("Failed to turn on...")
    return ConversationHandler.END


@verify_id
def off(update, context):
    global configuration

    if configuration["CurrentStatus"] == "OFF":
        return status(update, context)

    update.message.reply_text("Should turn bot OFF here...")
    if turn_off():
        update.message.reply_text("Turned Heat OFF.")
    else:
        update.message.reply_text("Failed to turn off...")
    return ConversationHandler.END


@verify_id
def force_on(update, context):
    global configuration

    if configuration["CurrentStatus"] == "ON":
        update.message.reply_text("HeatBot is already ON. Turning it ON anyways...")

    update.message.reply_text("Should turn bot ON here...")
    if turn_on():
        update.message.reply_text("Turned Heat ON.")
    else:
        update.message.reply_text("Failed to turn on...")
    return ConversationHandler.END


@verify_id
def force_off(update, context):
    global configuration

    if configuration["CurrentStatus"] == "OFF":
        update.message.reply_text("HeatBot is already OFF. Turning it OFF anyways...")

    update.message.reply_text("Should turn bot OFF here...")
    if turn_off():
        update.message.reply_text("Turned Heatbot OFF.")
    else:
        update.message.reply_text("Failed to turn off...")
    return ConversationHandler.END


@verify_id
def default(update, context):
    """Answer an unknown message"""
    update.message.reply_text("I didn't understand you. type /help for commands...")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.error(f"reason '{context.error}'. Update {update}")
    update.message.reply_text("An unknown error has occurred...")


def load_configuration():
    global configuration

    with open("configuration.json", "r") as conf:
        configuration = json.loads(conf.read())


def save_configuration():
    global configuration

    with open("configuration.json", "w") as conf:
        conf.write(json.dumps(configuration))


def main():
    global configuration
    load_configuration()

    """Start the bot."""
    updater = Updater(configuration["TelegramAccessToken"], use_context=True)
    dp = updater.dispatcher

    # Configure conversations
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("add", get_name),
                      CommandHandler("remove", remove_id),
                      CommandHandler("list", list_users),
                      CommandHandler("status", status),
                      CommandHandler("on", on),
                      CommandHandler("off", off),
                      CommandHandler("force_on", force_on),
                      CommandHandler("force_off", force_off),
                      CommandHandler("help", help),
                      CommandHandler("start", start),
                      CommandHandler('abort', abort)],
        states={
            ID: [MessageHandler(Filters.text, get_id)],
            ADD: [MessageHandler(Filters.text, add_user)],
            REMOVE_ID: [MessageHandler(Filters.text, remove)],
        },
        fallbacks=[CommandHandler('abort', abort)],
    )
    dp.add_handler(conversation_handler)

    # on non-command
    dp.add_handler(MessageHandler(Filters.text, default))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    logger.info("Starting Heatbot...")
    updater.start_polling()
    logger.info("Heatbot started!")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    logger.info("Heatbot stopped!")


if __name__ == '__main__':
    main()
