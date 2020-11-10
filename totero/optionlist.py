#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Pi-Yueh Chuang <pychuang@pm.me>
#
# Distributed under terms of the BSD 3-Clause license.

"""A window for options used for sorting."""
from typing import Sequence as _Sequence
from typing import List as _List
from typing import Union as _Union
from typing import Any as _Any
from urwid import AttrMap as _AttrMap
from urwid import ListBox as _ListBox
from urwid import SimpleFocusListWalker as _SimpleFocusListWalker
from urwid import Text as _Text
from urwid import Columns as _Columns
from urwid import Filler as _Filler
from urwid import Pile as _Pile
from urwid import LineBox as _LineBox
from urwid import connect_signal as _connect_signal
from .misc import DoneButton as _DoneButton
from .misc import CancelButton as _CancelButton


class OptionItem(_AttrMap):
    """A simple checkbox-like widget.

    Similar to urwid.CheckBox but simpiler. This one does not have cursor and does not allow a mix
    state.

    Parameters
    ----------
    tag : str
        The name/tag/content displayed.
    state : bool
        The initial state of the option.
    wrap : str
        See `urwid.Text`'s docstring.

    Attributes
    ----------
    signals : list of str
        The signals that are allowed to be emitted from this class. This should be a private
        attribute. But the current design in `urwid` requires it to be a public attribute.

    Color palette
    -------------
    1. Set `"opt item normal"` for options not on focus; alternatively, set this class'
       attribute `_norm_ctag` to change the color tag.
    2. Set `"opt item focus"` for options on focus; alternatively, set this class' attribute
       `_focus_ctagg` to change the color tag.
    """

    # default color tags in palette
    _norm_ctag = "opt item normal"
    _focus_ctag = "opt item focus"

    # marker
    _marker = {True: "X", False: " "}

    def __init__(self, tag: str, state: bool = False, wrap: str = "clip"):
        """Constructor. See class' docstring."""
        # initialize attributes
        self._tag = tag
        self._state = state

        # underlying widget
        txt = _Text("[{}] {}".format(self._marker[self._state], self._tag), wrap=wrap)
        txt.ignore_focus = False
        txt._selectable = True
        super().__init__(txt, self._norm_ctag, self._focus_ctag)

    def keypress(self, size: _Sequence[int], key: str) -> _Union[str, None]:
        """See the docstring of urwid.Widget.keypress."""
        # pylint: disable=unused-argument
        if key != "enter":
            return key
        self.flip_state()
        return None

    @property
    def tag(self) -> str:
        """The option name/tag."""
        return self._tag

    @property
    def state(self) -> bool:
        """The current state of this option"""
        return self._state

    @state.setter
    def state(self, value: bool) -> bool:
        """The current state of this option"""
        assert isinstance(value, bool)
        self._state = value
        self._invalidate()

    def flip_state(self):
        """Flip the current state."""
        self._state = (not self._state)
        self._invalidate()

    def _invalidate(self):
        """Override _invalidate."""
        self.original_widget.set_text("[{}] {}".format(self._marker[self._state], self._tag))
        super()._invalidate()


class OptionList(_AttrMap):
    """A list for options with cancel and confirmation buttons.

    After users click the *Done* button, the options that were selected can be retrieve using the
    `selected` property.

    Notes
    -----
    This widget also keeps a copy of the states of all options. But this copy of states does not
    change until users click the *Done* button.

    Parameters
    ----------
    options : a list-like of strings
        The contents of all options.
    states : bool or a list-like of bools
        The initial states of options. If a single bool, initialize all options with this state.
    title : str
        The title of this list window.
    wrap : str
        See `urwid.Text`'s docstring.

    Attributes
    ----------
    signals : list of str
        The signals that are allowed to be emitted from this class. This should be a private
        attribute. But the current design in `urwid` requires it to be a public attribute.

    Color palette
    -------------
    1. Set `"opt list title"` for the title; alternatively, set this class' attribute `_title_ctag`
       to change the color tag.
    2. Set `"opt list border"` for the border lines; alternatively, set this class' attribute
       `_border_ctagg` to change the color tag.
    """

    # signals that this widget may emit
    signals = ["close"]

    # the color tag
    _title_ctag = "opt list title"
    _border_ctag = "opt list border"

    def __init__(
        self, options: _Sequence[str], states: _Union[bool, _Sequence[bool]] = False,
        title: str = "", wrap: str = "clip"
    ):

        # initialize _SimpleFocusListWalker; it is actually a list-like object
        try:
            self._options = _SimpleFocusListWalker(
                [OptionItem(opt, state, wrap) for opt, state in zip(options, states)])
        except TypeError:
            self._options = _SimpleFocusListWalker(
                [OptionItem(opt, states, wrap) for opt in options])

        # the initial states of all options
        self._current_state = [opt.state for opt in self._options]

        # cancel and done (confirm) button
        self._buttons = _Columns([_CancelButton(), _DoneButton()])
        _connect_signal(self._buttons.widget_list[0], "cancel", self._cancel)
        _connect_signal(self._buttons.widget_list[1], "done", self._done)

        super().__init__(
            _LineBox(
                _Pile([_ListBox(self._options), (3, _Filler(self._buttons))]),
                title, "left", self._title_ctag
            ),
            self._border_ctag
        )

    def keypress(self, size: _Sequence[int], key: str):  # pylint: disable=unused-argument
        """See the docstring of urwid.Widget.keypress."""
        if self._command_map[key] == "exit program":  # ignore exit command
            return None
        return super().keypress(size, key)

    @property
    def selected(self) -> _List[str]:
        """Get the content of all selected options."""
        tags = []
        for state, widget in zip(self._current_state, self._options):
            if state:
                tags.append(widget.tag)
        return tags

    def _cancel(self, event: _Any):  # pylint: disable=unused-argument
        """Process cancel signal."""
        # if canceled, restore the original states
        for state, widget in zip(self._current_state, self._options):
            widget.state = state
        self._emit("close")

    def _done(self, event: _Any):  # pylint: disable=unused-argument
        """Process done signal."""
        self._current_state = [opt.state for opt in self._options]
        self._emit("close")
