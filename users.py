#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import ConversationHandler

import verifier
import heatbot
from configurations import Configuration


@verifier.verify_master
def get_name(update, context):
    update.message.reply_text("Please enter the name of the user you want to add.")
    return heatbot.ID  # Go to get_id


@verifier.verify_master
def get_id(update, context):
    name = update.message.text
    context.user_data["name_to_add"] = name
    update.message.reply_text(f"You are about to add '{name}'. Please enter their User ID. For example: '123456789'.")
    return heatbot.ADD  # Go to add_user


@verifier.verify_master
def add_user(update, context):
    user_id = update.message.text
    if user_id == "/abort":
        return heatbot.abort(update, context)

    if not user_id.isdecimal():
        update.message.reply_text(f"The User ID is invalid! It must contain numbers only! received: '{user_id}'.")
        update.message.reply_text(f"Please try again, or send /abort to abort operation.")
        return heatbot.ADD

    Configuration.Allowed[user_id] = context.user_data["name_to_add"]
    Configuration.save_configuration()
    heatbot.logger.info(f"Added new user: {Configuration.Allowed[user_id]} - {user_id}")
    if "name_to_add" in context.user_data:
        del context.user_data["name_to_add"]
    update.message.reply_text(f"User {Configuration.Allowed[user_id]} was added successfully!")
    return ConversationHandler.END  # Go the add_user


@verifier.verify_master
def remove_id(update, context):
    update.message.reply_text("Please enter the User ID of the user you want to remove. For example: '123456789'.")
    return heatbot.REMOVE_ID  # Go to remove


@verifier.verify_master
def remove(update, context):
    user_id = update.message.text
    if user_id == "/abort":
        return heatbot.abort(update, context)

    if not user_id.isdecimal():
        update.message.reply_text(f"The User ID is invalid! It must contain numbers only! received: '{user_id}'.")
        update.message.reply_text(f"Please try again, or send /abort to abort operation.")
        return heatbot.REMOVE_ID

    if user_id not in Configuration.Allowed:
        update.message.reply_text(f"The User ID '{user_id}' was not found in the allowed list.")
        update.message.reply_text(f"Please try again, or send /abort to abort operation.")
        return heatbot.REMOVE_ID

    name = Configuration.Allowed[user_id]
    del Configuration.Allowed[user_id]
    Configuration.save_configuration()
    heatbot.logger.info(f"Removed user: {name} - {user_id}")
    update.message.reply_text(f"User '{name}' was removed successfully!")
    return ConversationHandler.END


@verifier.verify_id
def list_users(update, context):
    message = "The following users are allowed to use this bot:"
    if len(Configuration.Allowed) <= 0:
        message += "\nNo users found."
    else:
        for user_id, user_name in Configuration.Allowed.items():
            message += "\n%20s - %s" % (user_name, user_id)
    update.message.reply_text(message)
    return ConversationHandler.END
