#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Pi-Yueh Chuang <pychuang@pm.me>
#
# Distributed under terms of the BSD 3-Clause license.

"""Miscellaneous functions.

Attributes
----------
command_map : urwid.CommandMap
    Custom command map shared by widgets.
default_theme : list of tuples of str/None
    Default color palette.
"""
from subprocess import Popen as _Popen
from subprocess import PIPE as _PIPE
from subprocess import DEVNULL as _DEVNULL
from pathlib import Path as _Path
from typing import Union as _Union
from time import sleep as _sleep
from urwid import Widget as _Widget
from urwid import ExitMainLoop as _ExitMainLoop
from urwid import CommandMap as _CommandMap

# define our own command map
command_map = _CommandMap()
command_map["j"] = command_map["down"]
command_map["k"] = command_map["up"]
command_map["ctrl d"] = command_map["page down"]
command_map["ctrl u"] = command_map["page up"]
command_map[" "] = "select"
command_map["q"] = "exit program"
_Widget._command_map = command_map

# default color palette
default_theme = [
    ("doc item normal", "white", "black", None, None, None),
    ("doc item focus", "black", "yellow", None, None, None),
    ("atthmnt win title", "light red,bold,italics", "black", None, None, None),
    ("atthmnt win border", "yellow", "black", None, None, None),
    ("atthmnt item normal", "white", "black", None, None, None),
    ("atthmnt item focus", "black", "yellow", None, None, None),
    ("cncl butn normal", "white", "black", None, None, None),
    ("cncl butn focus", "black", "yellow", None, None, None),
    ("cncl butn outline", "white", "black", None, None, None),
    ("doc list header", "white", "black", None, None, None),
    ("doc list divider", "white", "black", None, None, None),
]


def xdg_open(filepath: _Union[str, _Path], wait: int = 0):
    """Open a file with xdg-open.

    By default, the code check if the file is successfully opened by some application immediately
    after the subprocess is spawn. If yes, return the `Popen` object (which can access stdout &
    stderr). Otherwise. raise corresponding errors.

    Parameters
    ----------
    filepath : str or path-like
        The path to the file.
    wait : int
        How many second to wait before we check if the file is opened successfully

    Returns
    -------
    subprocess.Popen
        Note: the `poll()` method is already called once.

    Raises
    ------
    RuntimeError
        When `xdg-open` return following error codes: 1, 3, and 4.
    FileNotFoundError
        When `xdg-open` returns error code 2.

    """

    filepath = _Path(filepath).expanduser().resolve()
    result = _Popen(["xdg-open", filepath], stdin=_DEVNULL, stdout=_PIPE, stderr=_PIPE)

    _sleep(wait)
    status = result.poll()

    # something's weong
    if status == (1, 4):
        raise RuntimeError("The execution returns the following error:\n\n"+result.stderr)

    if status == 2:
        raise FileNotFoundError("{} does not exist!".format(filepath))

    if status == 3:
        raise RuntimeError("xdg-open does not know how to open {}".format(filepath))

    return result


def exit_trigger(key: str):
    """Check if this is the key to exit the program.

    Parameters
    ----------
    key : str
        A key string.
    """
    if command_map[key] == "exit program":
        raise _ExitMainLoop()
