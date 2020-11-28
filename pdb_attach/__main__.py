# -*- mode: python -*-
"""Pdb-attach client that can be run as a module."""
import argparse
import os
import socket
import sys

from .pdb_detach import _signal

PDB_PROMPT = "(Pdb) "

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "pid", type=int, metavar="PID", help="The pid of the process to debug."
)
parser.add_argument(
    "port",
    type=int,
    metavar="PORT",
    help="The port to connect to the running process.",
)
args = parser.parse_args()

os.kill(args.pid, _signal)
client = socket.create_connection(("localhost", args.port))
try:
    client_io = client.makefile("rw", buffering=1)
except TypeError:
    # Unexpected keyword argument. Try bufsize.
    client_io = client.makefile("rw", bufsize=1)  # type: ignore  # Python 2.7 compatibility.

first_command = True
while True:
    lines = []
    while True:
        line = client_io.readline(len(PDB_PROMPT))
        lines.append(line)
        if line == PDB_PROMPT:
            break

        if line == "":
            # The other side has closed the connection, so we can exit.
            print("Connection closed.")
            sys.exit(0)

    if first_command is not True:
        prompt = "".join(lines)
        try:
            to_server = raw_input(lines)  # type: ignore  # Python 2.7 compatibility.
        except NameError:
            # Ignore flake8 warning about input in Python 2.7 since we are checking for raw_input first.
            to_server = input("".join(lines))  # noqa: S322

        if to_server[-1] != "\n":
            to_server += "\n"

        client_io.write(to_server)
    else:
        # For some reason the debugger starts in the __repr__ method of the
        # socket, so counteract this by jumping up a frame.
        client_io.write("u\n")
        first_command = False
