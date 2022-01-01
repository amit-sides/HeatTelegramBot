#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json


class DynamicConfiguration:
    def __init__(self, cls, args, _):
        pass

    @classmethod
    def load_configuration(cls):
        with open("configuration.json", "r") as conf:
            cls.__configuration = json.loads(conf.read())

    @classmethod
    def save_configuration(cls):
        with open("configuration.json", "w") as conf:
            conf.write(json.dumps(cls.__configuration))

    @classmethod
    def __getattr__(cls, key):
        return cls.__configuration[key]

    @classmethod
    def __setattr__(cls, key, value):
        cls.__configuration[key] = value


class Configuration(metaclass=DynamicConfiguration):
    __configuration = None
