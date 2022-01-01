#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import ConversationHandler

from configurations import Configuration


def verify_id(func):
    def verifier(update, context):
        if update.message is None or update.message.from_user is None:
            return ConversationHandler.END

        user = update.message.from_user
        user_id = str(user["id"])
        if user_id not in Configuration.Allowed:
            update.message.reply_text(f"You are not allowed to use this bot! Your user id is: {user_id}.")
            heatbot.logger.warning(f"Unknown user interacting with the bot. User ID: {user_id}.")
            return ConversationHandler.END
        return func(update, context)

    return verifier


def verify_master(func):
    def verifier(update, context):
        if update.message is None or update.message.from_user is None:
            return ConversationHandler.END

        user = update.message.from_user
        user_id = str(user["id"])
        if user_id != Configuration.MasterID:
            update.message.reply_text("You are not allowed to use this command! Only the master shall do that!")
            heatbot.logger.warning(f"User trying to impersonate Master. User ID: {user_id}.")
            return ConversationHandler.END
        return func(update, context)

    return verifier


import heatbot  # Needs to be here to solve circular imports of decorators
