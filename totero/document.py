#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Pi-Yueh Chuang <pychuang@pm.me>
#
# Distributed under terms of the BSD 3-Clause license.

"""Widgets related to documents."""
from copy import deepcopy as _deepcopy
from typing import Sequence as _Sequence
from typing import Any as _Any
from typing import Optional as _Optional
from pandas import Series as _Series
from urwid import Columns as _Columns
from urwid import AttrMap as _AttrMap
from urwid import Text as _Text
from urwid import CompositeCanvas as _CompositeCanvas
from urwid import connect_signal as _connect_signal
from .attachment import AttachmentItem as _AttachmentItem
from .attachment import AttachmentSelectionPopUP as _AttachmentSelectionPopUP


class DocumentItem(_AttrMap):
    """A row item that represents one document in Zotero.

    One single line widget that can control what column to show.

    Parameters
    ----------
    data : pandas.Series
        The raw data of a document with brief info. The `pandas.Series` should have at least the
        indices requested by `columns`. This widget makes a deep copy of the `data`.
    columns : list of str, or None
        The columns to be shown when rendered. The keys in `columns` should be valid indices of the
        `data`. If `None`, use all indices from `data`.
    weights : list of int, or None
        The weights of the column widths. If None, assume all column widths are the same. If
        `weights` is provided, it should have the same langth as the `columns`.
    wrap : str
        The `wrap` argument in a `urwid.Text` widget. Whether the texts insides columns should be
        wrapped if longer than the column widths.

    Notes
    -----
    1. The underlying widget is `urwid.Column` with *selectable* `uriwd.Text`s. Because of
       `urwid.Text`, the sizing mode of this widget is `flow` type.
    2. Because of the `urwid.Text`, users have to make sure all data can be converted to `str`.
    3. If the key `"attachment path"` is provided in `data`, and its value is a list of
       paths/strings:
        a. If length of this list >= 2, when key in "enter", a window pops up and allows users to
           choose which attachment to open.
        b. If length of this list == 1, when key in "enter", the attachment will be opened with
           `xdg-open`
        c. If it is an empty list, nothing happens.
    4. If the value to `"attachment path"` is a single str/path, then it's the same as providing a
       length-one list.
    5. To enable the attachment selection pop-up, the major render loop `urwid.MainLoop` should
       have the `pop_ups` argument enabled.

    Color palette
    -------------
    1. Set `"doc item normal"` for an item not on focus; alternatively, set this class'
       attribute `_normal_ctag` to change the tag from `"doc item normal"` to another tag.
    2. Set `"doc item focus"` for an item on focus; alternatively, set this class' attribute
       `_focus_ctag` to change the tag from `"doc item focus"` to another tag.

    Examples
    --------
    >>> from pandas import Series
    >>> from urwid import MainLoop, ListBox, SimpleFocusListWalker
    >>> from totero import DocumentItem
    >>> item1 = Series({
            "author": "Abc et al.",
            "year": 2020,
            "title": "An example document 1",
            "publication": "Journal of Examples",
            "attachment path": "~/example1.pdf"
        })
    >>> item2 = Series({
            "author": "Def et al.",
            "year": 2019,
            "title": "An example document 2",
            "publication": "Journal of Examples",
            "attachment path": ["~/example2.pdf", "~/example3.pdf"]
        })
    >>> doc1 = DocumentItem(item1, ["author", "title", "publication", "year"], [20, 100, 30, 6])
    >>> doc2 = DocumentItem(item2, ["author", "title", "publication", "year"], [20, 100, 30, 6])
    >>> colors = [
            ("doc item normal", "white", "black"), ("doc item focus", "black", "yellow"),
            ("atthmnt win title", "light red,bold,italics", "black"),
            ("atthmnt item normal", "white", "black"), ("atthmnt item focus", "black", "yellow"),
            ("cncl butn normal", "white", "black"), ("cncl butn focus", "black", "yellow"),
        ]
    >>> loop = MainLoop(ListBox(SimpleFocusListWalker([doc1, doc2])), colors, pop_ups=True)
    >>> loop.run()

    Use the arrow keys (up & down, or any custom keys that map to up and down) to select a different
    document and "enter" to open the attachment selection pop-up.
    """

    # color tag
    _normal_ctag = "doc item normal doc"
    _focus_ctag = "doc item focus"

    def __init__(
        self, data: _Series, columns: _Optional[_Sequence[str]] = None,
        weights: _Optional[_Sequence[int]] = None, wrap: str = "clip",
    ):
        # sanity check
        assert isinstance(data, _Series), "`data` should be a pandas.Series."

        # initialize parent with a placeholde/fake widget
        super().__init__(_Text(""), self._normal_ctag, self._focus_ctag)

        # make a reference to data
        self._data = _deepcopy(data)

        # save the option
        self._wrap = wrap

        # initial attachment windows status
        self._attachment_win = None

        # initialize the copy of columns and weights
        self._columns = None
        self._weights = None

        # set columns and weights, re-create the underlying Column widget, and re-render
        self.reset_columns(columns, weights)

    def render(self, size: _Sequence[int], focus: bool = False):
        """See the docstring of urwid.Widget.render."""
        canv = super().render(size, focus)
        if self._attachment_win is not None:
            canv = _CompositeCanvas(canv)
            canv.set_pop_up(*self._attachment_win)
        return canv

    def keypress(self, size: _Sequence[int], key: str):  # pylint: disable=unused-argument
        """See the docstring of urwid.Widget.keypress."""
        if key == "enter":
            return self._handle_attachment_triger()

        return key

    def reset_columns(
        self,
        columns: _Optional[_Sequence[str]] = None,
        weights: _Optional[_Sequence[int]] = None
    ):
        """Reset the columns to be rendered.

        Parameters
        ----------
        columns : list of str, or None
            See the constructor's parameters in the class docstring.
        weights : list of int, or None
            See the constructor's parameters in the class docstring.
        """

        # if no columns are provided, show all columns
        if columns is None:
            self._columns = self._data.index.to_list()
        else:
            self._columns = _deepcopy(columns)

        # if no weights provided, use equal widths
        if weights is None:
            self._weights = [1] * len(self._columns)
        else:
            self._weights = _deepcopy(weights)

        # underlying widget; a urwid.Column; will be saved as self._original_widget after __init__
        cols = [
            ("weight", w, _Text(str(self._data.loc[k]), wrap=self._wrap))
            for w, k in zip(self._weights, self._columns)
        ]
        cols = _Columns(cols, dividechars=1)
        cols.ignore_focus = False
        cols._selectable = True  # pylint: disable=protected-access

        # reset and rerender
        self._set_original_widget(cols)

    def reset_data(self, data: _Series):
        """Reset the underlying pandas.Series."""
        self._data = _deepcopy(data)
        self.reset_columns(self._columns, self._weights)

    def _handle_attachment_triger(self):
        """Create a pop-up window widget."""

        # make a reference for shorter code
        try:
            raw_atta = self._data.loc["attachment path"]
        except KeyError:
            return None

        # try if it's a str or path-like
        try:
            return _AttachmentItem(raw_atta).keypress((None,), "enter")
        except TypeError:  # neither a str nor a path-like
            pass

        # then we assume it's a list or tuple or any iteratable
        if len(raw_atta) == 0:
            return None

        if len(raw_atta) == 1:
            _AttachmentItem(raw_atta).keypress((None,), "enter")

        self._attachment_win = [_AttachmentSelectionPopUP(raw_atta)]
        self._attachment_win.extend([1, 1, 100, len(raw_atta)+5])
        _connect_signal(self._attachment_win[0], "close", self._clear_pop_up)
        self._invalidate()
        return None

    def _clear_pop_up(self, event: _Any):  # pylint: disable=unused-argument
        """Remove the pop-up attachment selection window.

        Parameters
        ----------
        event : any
            Not used here. Just for compatibility with other signal callbacks.
        """
        self._attachment_win = None
        self._invalidate()

    def __str__(self):
        return str(self._data.to_list())
