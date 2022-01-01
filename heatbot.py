#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import BotCommand, KeyboardButton, ReplyKeyboardMarkup

from configurations import Configuration
import verifier
import users
import commands

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

ID, ADD, REMOVE_ID = range(3)


def abort(update, context):
    if "name_to_add" in context.user_data:
        del context.user_data["name_to_add"]
    update.message.reply_text("Operation aborted.")
    return ConversationHandler.END


@verifier.verify_id
def start(update, context):
    keyboard = [[KeyboardButton("Help 🤷‍♂️"), KeyboardButton("Status ❔")],
                [KeyboardButton("ON 💡"), KeyboardButton("OFF 🍗")]]
    markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text("Hi! I'm your HeatBot!\nI'm here to help you turn your heater on and off :)",
                              reply_markup=markup)
    return ConversationHandler.END


@verifier.verify_id
def default(update, context):
    """Answer an unknown message"""
    print(update.message.text)
    update.message.reply_text("I didn't understand you. type /help for commands...")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.error(f"reason '{context.error}'. Update {update}")
    if update.message:
        update.message.reply_text("An unknown error has occurred...")


@verifier.verify_id
def help(update, context):
    help_message = AVAILABLE_COMMANDS

    user = update.message.from_user
    user_id = str(user["id"])
    if user_id == Configuration.MasterID:
        help_message += MASTER_COMMANDS

    help_message += LAST_COMMANDS
    update.message.reply_text(help_message)


def main():
    Configuration.load_configuration()

    """Start the bot."""
    updater = Updater(Configuration.TelegramAccessToken, use_context=True)
    dp = updater.dispatcher
    word_regex = lambda word: Filters.regex(f"^(.*\s+)?{word}(\s+.*)?$")

    # Configure conversations
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("add", users.get_name),
                      CommandHandler("remove", users.remove_id),
                      CommandHandler("list", users.list_users),
                      CommandHandler("status", commands.status),
                      MessageHandler(word_regex("[sS]tatus"), commands.status),
                      CommandHandler("on", commands.on),
                      MessageHandler(word_regex("[oO][nN]"), commands.on),
                      CommandHandler("off", commands.off),
                      MessageHandler(word_regex("[oO][fF][fF]"), commands.off),
                      CommandHandler("force_on", commands.force_on),
                      CommandHandler("force_off", commands.force_off),
                      CommandHandler("help", help),
                      MessageHandler(word_regex("[hH]elp"), help),
                      CommandHandler("start", start),
                      CommandHandler('abort', abort)],
        states={
            ID: [MessageHandler(Filters.text, users.get_id)],
            ADD: [MessageHandler(Filters.text, users.add_user)],
            REMOVE_ID: [MessageHandler(Filters.text, users.remove)],
        },
        fallbacks=[CommandHandler('abort', abort)],
    )
    dp.add_handler(conversation_handler)

    # Handler for non-commands
    dp.add_handler(MessageHandler(Filters.text, default))

    # Log errors
    dp.add_error_handler(error)

    # Configure bot commands (for auto-completion)
    bot_commands = [BotCommand(command="start", description="Starts interaction with HeatBot."),
                    BotCommand(command="on", description="Turns the heat on."),
                    BotCommand(command="off", description="Turns the heat off."),
                    BotCommand(command="status", description="Shows the status of the HeatBot."),
                    BotCommand(command="help", description="Shows a list of all commands.")]
    updater.bot.set_my_commands(bot_commands)

    # Start the Bot
    logger.info("Starting Heatbot...")
    updater.start_polling()
    logger.info("Heatbot started!")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    logger.info("Heatbot stopped!")


if __name__ == "__main__":
    main()
