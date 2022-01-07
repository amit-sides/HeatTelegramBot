#!/bin/bash

# Install pybluez and its dependencies
sudo apt-get install python3-pip
sudo apt-get install python-dev libbluetooth-dev
pip3 install pybluez

# Install gattlib and its dependencies
sudo apt install pkg-config libboost-python-dev libboost-thread-dev libbluetooth-dev libglib2.0-dev python-dev
pip3 install gattlib