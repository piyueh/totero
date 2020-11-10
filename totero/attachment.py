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
from urwid import AttrMap as _AttrMap
from urwid import Text as _Text
from urwid import LineBox as _LineBox
from urwid import ListBox as _ListBox
from urwid import Columns as _Columns
from urwid import SimpleFocusListWalker as _SimpleFocusListWalker
from urwid import connect_signal as _connect_signal
from .misc import xdg_open as _xdg_open
from .misc import CancelButton as _CancelButton


class AttachmentItem(_AttrMap):
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

    Color palette
    -------------
    1. Set `"atthmnt item normal"` for the items not on focus; alternatively, set this class'
       attribute `_norm_ctag` to change the color tag.
    2. Set `"atthmnt item focus"` for the items on focus; alternatively, set this class' attribute
       `_focus_ctagg` to change the color tag.
    """

    # register signals
    signals = ["done"]

    # default color tags in palette
    _norm_ctag = "atthmnt item normal"
    _focus_ctag = "atthmnt item focus"

    def __init__(self, path: _Union[str, _Path], wrap: str = "clip"):
        """Constructor. See class' docstring."""
        self._path = _Path(path).expanduser().resolve()
        self._txt = _Text("    \u2192 "+str(self._path.name), wrap=wrap)
        self._txt.ignore_focus = False
        self._txt._selectable = True
        super().__init__(self._txt, self._norm_ctag, self._focus_ctag)

    def keypress(self, size: _Sequence[int], key: str) -> _Union[str, None]:
        """See the docstring of urwid.Widget.keypress."""
        # pylint: disable=unused-argument
        if key != "enter":
            return key

        _xdg_open(self._path)
        self._emit("done")
        return None


class AttachmentSelectionPopUP(_AttrMap):
    """A Pop-up box containing a list of attachments.

    Only pop-up when there are more than one attachment in the list. If there's only one attachment,
    the widget will directly pass the key code to the only AttachmentItem.

    Parameters
    ----------
    attachments : list of str, list of path-like, or a list of AttachmentItem
        The absolute paths to attachments.

    Attributes
    ----------
    signals : list of str
        The signals that are allowed to be emitted from this class. This should be a private
        attribute. But the current design in `urwid` requires it to be a public attribute.

    Color palette
    -------------
    1. Set `"atthmnt win title"` title font attributes. Alternatively, set the class' attribute
       `_title_ctag` to change the color tag.
    2. Set `"atthmnt win border"` for border lines. Alternatively, set this class' attribute
       `_border_line_ctag` to change the color tag.
    """

    # register signals
    signals = ["close"]

    # default color tags in palette
    _title_ctag = "atthmnt win title"
    _border_line_ctag = "atthmnt win border"

    def __init__(self, attachments: _Sequence[_Union[str, _Path]]):
        """Constructor. See class' docstring."""

        # the cancel button
        button = _CancelButton()
        _connect_signal(button, 'cancel', lambda button: self._emit("close"))
        last_row = _Columns([_Text(""), (10, button)], 1)

        # convert strings/paths to AttachmentItem list
        data = []
        for att in attachments:
            data.append(att if isinstance(att, AttachmentItem) else AttachmentItem(att))
            _connect_signal(data[-1], 'done', lambda button: self._emit("close"))

        super().__init__(
            _LineBox(
                _ListBox(_SimpleFocusListWalker([*data, last_row])),
                "Multiple attachments found. Select one to open.",
                "left", self._title_ctag
            ), self._border_line_ctag
        )
