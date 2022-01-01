#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from telegram.ext import ConversationHandler
import switchbot_py3

import verifier
from configurations import Configuration


def get_status():
    last_change = datetime.datetime.fromtimestamp(Configuration.LastChange)
    last_change_duration = datetime.datetime.now() - last_change
    hours = last_change_duration.seconds // 3600 + last_change_duration.days * 24
    minutes = (last_change_duration.seconds // 60) % 60

    duration_string = ""
    if hours > 1:
        duration_string += f"{hours} hours and "
    elif hours == 1:
        duration_string += f"{hours} hour and "
    duration_string += f"{minutes} minutes"

    if Configuration.CurrentStatus == "ON":
        status = f"The heat has been ON for {duration_string}."
    elif Configuration.CurrentStatus == "OFF":
        status = f"The heat has been OFF for {duration_string}."
    else:
        status = f"Current Status: UNKNOWN.\nLast status change: {duration_string} ago."
    return status


@verifier.verify_id
def status(update, context):
    update.message.reply_text(get_status())
    return ConversationHandler.END


def turn_on():
    switchbot_driver = switchbot_py3.Driver(Configuration.BluetoothAddress,
                                            Configuration.BluetoothInterface)
    switchbot_driver.run_command("on")  # TODO: Check return value

    Configuration.CurrentStatus = "ON"
    Configuration.LastChange = datetime.datetime.now().timestamp()
    Configuration.save_configuration()
    return True


def turn_off():
    switchbot_driver = switchbot_py3.Driver(Configuration.BluetoothAddress,
                                            Configuration.BluetoothInterface)
    switchbot_driver.run_command("off")  # TODO: Check return value

    Configuration.CurrentStatus = "OFF"
    Configuration.LastChange = datetime.datetime.now().timestamp()
    Configuration.save_configuration()
    return True


@verifier.verify_id
def on(update, context):
    if Configuration.CurrentStatus == "ON":
        return status(update, context)

    update.message.reply_text("Should turn bot ON here...")
    if turn_on():
        update.message.reply_text("Turned Heatbot ON.")
    else:
        update.message.reply_text("Failed to turn on...")
    return ConversationHandler.END


@verifier.verify_id
def off(update, context):
    if Configuration.CurrentStatus == "OFF":
        return status(update, context)

    update.message.reply_text("Should turn bot OFF here...")
    if turn_off():
        update.message.reply_text("Turned Heat OFF🍗.")
    else:
        update.message.reply_text("Failed to turn off...")
    return ConversationHandler.END


@verifier.verify_id
def force_on(update, context):
    if Configuration.CurrentStatus == "ON":
        update.message.reply_text("HeatBot is already ON💡. Turning it ON anyways...")

    update.message.reply_text("Should turn bot ON here...")
    if turn_on():
        update.message.reply_text("Turned Heat ON💡.")
    else:
        update.message.reply_text("Failed to turn on...")
    return ConversationHandler.END


@verifier.verify_id
def force_off(update, context):
    if Configuration.CurrentStatus == "OFF":
        update.message.reply_text("HeatBot is already OFF🍗. Turning it OFF anyways...")

    update.message.reply_text("Should turn bot OFF here...")
    if turn_off():
        update.message.reply_text("Turned Heatbot OFF.")
    else:
        update.message.reply_text("Failed to turn off...")
    return ConversationHandler.END
