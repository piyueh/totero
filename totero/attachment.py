#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Pi-Yueh Chuang <pychuang@pm.me>
#
# Distributed under terms of the BSD 3-Clause license.

"""Attachment-related widgets."""
from typing import Sequence as _Sequence
from typing import Union as _Union
from pathlib import Path as _Path
from subprocess import Popen as _Popen
from subprocess import PIPE as _PIPE
from subprocess import DEVNULL as _DEVNULL
from urwid import AttrMap as _AttrMap
from urwid import Text as _Text
from urwid import LineBox as _LineBox
from urwid import ListBox as _ListBox
from urwid import Columns as _Columns
from urwid import SimpleFocusListWalker as _SimpleFocusListWalker
from urwid import connect_signal as _connect_signal


class CancelButton(_AttrMap):
    """A cancel button.

    This is a specialized button that everything is hard-coded, except the display attributes.

    Attributes
    ----------
    signals : list of str
        The signals that are allowed to be emitted from this class. This should be a private
        attribute. But the current design in `urwid` requires it to be a public attribute.
    """

    # register signals
    signals = ["close"]

    # default color tags in palette
    _button_norm_ctag = "normal button"
    _button_focus_ctag = "selected button"
    _button_outline_ctag = "button outline"

    def __init__(self):
        """Constructor. See class' docstring."""
        self._txt = _Text("Cancel", "center", "clip")
        self._txt.ignore_focus = False
        self._txt._selectable = True
        self._txt = _AttrMap(self._txt, self._button_norm_ctag, self._button_focus_ctag)
        super().__init__(_LineBox(self._txt), self._button_outline_ctag)

    def keypress(self, size: _Sequence[int], key: str) -> _Union[str, None]:
        """See the docstring of urwid.Widget.keypress."""
        # pylint: disable=unused-argument
        if key == "enter":
            self._emit("close")
            return None
        return key


class AttachmetnItem(_AttrMap):
    """A row item that represents an attachment.

    This widget stors the full path to an attachment but displays only the file name. When "enter"
    key input is provided, it opens the attachments with `xdg-open`.

    Parameters
    ----------
    path : str or path-like
        The absolute path to an attachment.
    wrap : str
        See the `wrap` argument in `urwid.Text`.

    Attributes
    ----------
    signals : list of str
        The signals that are allowed to be emitted from this class. This should be a private
        attribute. But the current design in `urwid` requires it to be a public attribute.
    """

    # register signals
    signals = ["close"]

    # default color tags in palette
    _atta_norm_ctag = "normal doc"
    _atta_focus_ctag = "selected doc"

    def __init__(self, path: _Union[str, _Path], wrap: str = "clip"):
        """Constructor. See class' docstring."""
        self._path = _Path(path)
        self._txt = _Text("    \u231e "+str(self._path.name), wrap=wrap)
        self._txt.ignore_focus = False
        self._txt._selectable = True
        super().__init__(self._txt, self._atta_norm_ctag, self._atta_focus_ctag)

    def keypress(self, size: _Sequence[int], key: str) -> _Union[str, None]:
        """See the docstring of urwid.Widget.keypress."""
        # pylint: disable=unused-argument
        if key != "enter":
            return key

        # for enter: rely on xdg-open to open the attachment
        _Popen(["xdg-open", self._path], stdin=_DEVNULL, stdout=_PIPE, stderr=_PIPE)
        self._emit("close")
        return None


class AttachmentSelectionPopUP(_LineBox):
    """A Pop-up box containing a list of attachments.

    Parameters
    ----------
    attachments : a list of str or a list of path-like
        The absolute paths to attachments.

    Attributes
    ----------
    signals : list of str
        The signals that are allowed to be emitted from this class. This should be a private
        attribute. But the current design in `urwid` requires it to be a public attribute.
    """

    # register signals
    signals = ["close"]

    # default color tags in palette
    _title_ctag = "attachment win title"

    def __init__(self, attachments: _Sequence[_Union[str, _Path]]):
        """Constructor. See class' docstring."""

        button = CancelButton()
        last_row = _Columns([_Text(""), (10, button)], 1)

        # if a child widget sends "close" signal, this widget also sends "close" to the parent
        _connect_signal(button, 'close', lambda button: self._emit("close"))
        for att in attachments:
            _connect_signal(att, 'close', lambda button: self._emit("close"))

        super().__init__(
            _ListBox(_SimpleFocusListWalker([*attachments, last_row])),
            "Multiple attachments found. Select one to open.",
            "left", self._title_ctag
        )
