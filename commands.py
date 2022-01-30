#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import time

from telegram.ext import ConversationHandler
import switchbot_py3

import heatbot
import verifier
from configurations import Configuration

LOG = list()
LOG_SIZE = 15
AUTOMATIC_OFF_THREAD_INTERVALS = 5 * 60  # 5 Minutes
AUTOMATIC_OFF_THREAD_SLEEP = 5  # 5 Seconds

def add_to_log(update, action):
    global LOG

    if update is None:
        name = "System"
    else:
        user = update.message.from_user
        user_id = str(user["id"])
        name = Configuration.Allowed[user_id]

    current_time = datetime.datetime.now().strftime("%d.%m %H:%M")
    LOG.append((name, current_time, action))
    if len(LOG) >= LOG_SIZE:
        LOG.pop(0)

    heatbot.logger.info(f"{name} used action '{action}'.")


def get_log(is_master=False):
    global LOG

    log_output = "Logs:\n"
    if len(LOG) == 0:
        return log_output + "     None."

    for name, current_time, action in LOG:
        if is_master:
            log_output += "%10s : " % (name,)
        log_output += f"{current_time} - {action}.\n"
    return log_output[:-1]


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
        status_message = f"The heat has been ON for {duration_string}."
    elif Configuration.CurrentStatus == "OFF":
        status_message = f"The heat has been OFF for {duration_string}."
    else:
        status_message = f"Current Status: UNKNOWN.\nLast status change: {duration_string} ago."
    return status_message


@verifier.verify_id
def status(update, context):
    update.message.reply_text(get_status())
    add_to_log(update, "status")
    return ConversationHandler.END

@verifier.verify_id
def log(update, context):
    user = update.message.from_user
    user_id = str(user["id"])

    update.message.reply_text(get_log(user_id == Configuration.MasterID))
    add_to_log(update, "log")
    return ConversationHandler.END


def turn_on():
    switchbot_driver = switchbot_py3.Driver(Configuration.BluetoothAddress,
                                            Configuration.BluetoothInterface)
    return_code = switchbot_driver.run_command("on")
    if return_code != [b'\x13']:
        return False

    Configuration.CurrentStatus = "ON"
    Configuration.LastChange = datetime.datetime.now().timestamp()
    Configuration.save_configuration()
    return True


def turn_off():
    switchbot_driver = switchbot_py3.Driver(Configuration.BluetoothAddress,
                                            Configuration.BluetoothInterface)
    return_code = switchbot_driver.run_command("off")
    if return_code != [b'\x13']:
        return False

    Configuration.CurrentStatus = "OFF"
    Configuration.LastChange = datetime.datetime.now().timestamp()
    Configuration.save_configuration()
    return True


@verifier.verify_id
def on(update, context):
    if Configuration.CurrentStatus == "ON":
        return status(update, context)

    if turn_on():
        update.message.reply_text("Turned Heatbot ON 💡")
        add_to_log(update, "on")
    else:
        update.message.reply_text("Failed to turn on...")
    return ConversationHandler.END


@verifier.verify_id
def off(update, context):
    if Configuration.CurrentStatus == "OFF":
        return status(update, context)

    if turn_off():
        update.message.reply_text("Turned Heat OFF 🍗")
        add_to_log(update, "off")
    else:
        update.message.reply_text("Failed to turn off...")
    return ConversationHandler.END


@verifier.verify_id
def force_on(update, context):
    if Configuration.CurrentStatus == "ON":
        update.message.reply_text("HeatBot is already ON 💡. Turning it ON anyways...")

    if turn_on():
        update.message.reply_text("Turned Heat ON 💡")
        add_to_log(update, "force on")
    else:
        update.message.reply_text("Failed to turn on...")
    return ConversationHandler.END


@verifier.verify_id
def force_off(update, context):
    if Configuration.CurrentStatus == "OFF":
        update.message.reply_text("HeatBot is already OFF 🍗. Turning it OFF anyways...")
    
    if turn_off():
        update.message.reply_text("Turned Heatbot OFF.")
        add_to_log(update, "force off")
    else:
        update.message.reply_text("Failed to turn off...")
    return ConversationHandler.END

def async_automatic_off(should_stop_event):
    while not should_stop_event.is_set():
        for _ in range(AUTOMATIC_OFF_THREAD_INTERVALS // AUTOMATIC_OFF_THREAD_SLEEP):
            time.sleep(AUTOMATIC_OFF_THREAD_SLEEP)
            if should_stop_event.is_set():
                return

        if Configuration.CurrentStatus != "ON":
            continue
        if Configuration.AutomaticOffInMinutes is None:
            continue

        now = datetime.datetime.now()
        last_change = datetime.datetime.fromtimestamp(Configuration.LastChange)
        minutes_since_last_change = (now - last_change).total_seconds() / 60
        if minutes_since_last_change >= Configuration.AutomaticOffInMinutes:
            if turn_off():
                add_to_log(None, "automatic off")
            else:
                heatbot.logger.warning("Automatic off failed")
