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
from typing import Sequence as _Sequence
from time import sleep as _sleep
from urwid import Widget as _Widget
from urwid import AttrMap as _AttrMap
from urwid import Text as _Text
from urwid import LineBox as _LineBox
from urwid import ExitMainLoop as _ExitMainLoop
from urwid import CommandMap as _CommandMap

# define our own command map
command_map = _CommandMap()
command_map["j"] = command_map["down"]
command_map["k"] = command_map["up"]
command_map["h"] = command_map["left"]
command_map["l"] = command_map["right"]
command_map["ctrl d"] = command_map["page down"]
command_map["ctrl u"] = command_map["page up"]
command_map["q"] = "exit program"
_Widget._command_map = command_map  # pylint: disable=protected-access

# default color palette
default_theme = [
    ("opt item normal", "white", "black", None, None, None),
    ("opt item focus", "black", "yellow", None, None, None),
    ("opt win", "white", "black", None, None, None),
    ("doc item normal", "white", "black", None, None, None),
    ("doc item focus", "black", "yellow", None, None, None),
    ("atthmnt win title", "light red,bold,italics", "black", None, None, None),
    ("atthmnt win border", "yellow", "black", None, None, None),
    ("atthmnt item normal", "white", "black", None, None, None),
    ("atthmnt item focus", "black", "yellow", None, None, None),
    ("cncl butn normal", "white", "black", None, None, None),
    ("cncl butn focus", "black", "yellow", None, None, None),
    ("cncl butn outline", "white", "black", None, None, None),
    ("done butn normal", "white", "black", None, None, None),
    ("done butn focus", "black", "yellow", None, None, None),
    ("done butn outline", "white", "black", None, None, None),
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


class CancelButton(_AttrMap):
    """A cancel button.

    This is a specialized button that everything is hard-coded, except the display attributes.

    Attributes
    ----------
    signals : list of str
        The signals that are allowed to be emitted from this class. This should be a private
        attribute. But the current design in `urwid` requires it to be a public attribute.

    Color palette
    -------------
    1. Set `"cncl butn normal"` for the buttons not on focus; alternatively, set this class'
       attribute `_nrom_ctag` to change the color tag.
    2. Set `"cncl butn focus"` for the buttons on focus; alternatively, set this class' attribute
       `_focus_ctag` to change the color tag.
    3. Set `"cncl butn outline"` for buttons' border lines; alternatively, set this class' attribute
       `_outline_ctag` to change the color tag.
    """

    # register signals
    signals = ["cancel"]

    # default color tags in palette
    _norm_ctag = "cncl butn normal"
    _focus_ctag = "cncl butn focus"
    _outline_ctag = "cncl butn outline"

    def __init__(self):
        """Constructor. See class' docstring."""
        self._txt = _Text("Cancel", "center", "clip")
        self._txt.ignore_focus = False
        self._txt._selectable = True
        self._txt = _AttrMap(self._txt, self._norm_ctag, self._focus_ctag)
        super().__init__(_LineBox(self._txt), self._outline_ctag)

    def keypress(self, size: _Sequence[int], key: str) -> _Union[str, None]:
        """See the docstring of urwid.Widget.keypress."""
        # pylint: disable=unused-argument
        if key == "enter":
            self._emit("cancel")
            return None
        return key


class DoneButton(_AttrMap):
    """A done button.

    This is a specialized button that everything is hard-coded, except the display attributes.

    Attributes
    ----------
    signals : list of str
        The signals that are allowed to be emitted from this class. This should be a private
        attribute. But the current design in `urwid` requires it to be a public attribute.

    Color palette
    -------------
    1. Set `"done butn normal"` for the buttons not on focus; alternatively, set this class'
       attribute `_nrom_ctag` to change the color tag.
    2. Set `"done butn focus"` for the buttons on focus; alternatively, set this class' attribute
       `_focus_ctag` to change the color tag.
    3. Set `"done butn outline"` for buttons' border lines; alternatively, set this class' attribute
       `_outline_ctag` to change the color tag.
    """

    # register signals
    signals = ["done"]

    # default color tags in palette
    _norm_ctag = "done butn normal"
    _focus_ctag = "done butn focus"
    _outline_ctag = "done butn outline"

    def __init__(self):
        """Constructor. See class' docstring."""
        self._txt = _Text("Done", "center", "clip")
        self._txt.ignore_focus = False
        self._txt._selectable = True
        self._txt = _AttrMap(self._txt, self._norm_ctag, self._focus_ctag)
        super().__init__(_LineBox(self._txt), self._outline_ctag)

    def keypress(self, size: _Sequence[int], key: str) -> _Union[str, None]:
        """See the docstring of urwid.Widget.keypress."""
        # pylint: disable=unused-argument
        if key == "enter":
            self._emit("done")
            return None
        return key
