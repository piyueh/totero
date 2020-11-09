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
from typing import Mapping as _Mapping
from typing import Any as _Any
from typing import Optional as _Optional
from typing import Union as _Union
from pandas import Series as _Series
from urwid import Columns as _Columns
from urwid import AttrMap as _AttrMap
from urwid import Text as _Text
from urwid import CompositeCanvas as _CompositeCanvas
from urwid import connect_signal as _connect_signal
from .attachment import AttachmetnItem as _AttachmetnItem
from .attachment import AttachmentSelectionPopUP as _AttachmentSelectionPopUP


class DocumentItem(_AttrMap):
    """A row item that represents one document in Zotero.

    One single line widget that can control what column to show.

    Parameters
    ----------
    data : dict or pandas.Series
        The raw data of a document with brief info. The provided `dict`/`pandas.Series` should have
        at least the indices requested by `columns`.
    columns : list of str, or None
        The columns to be shown when rendered. The keys in `columns` should be valid keys or column
        names of the `data`. If `None`, use all keys (except attachments) from `data`.
    weights : list of int, or None
        The weights of the column widths. If None, assume all column widths are the same. If
        `weights` is provided, it should have the same langth as the `columns`.
    wrap : str
        The `wrap` argument in a `urwid.Text` widget. Whether the texts insides columns should be
        wrapped if longer than the column widths.

    Notes
    -----
    1. The underlying widget is `urwid.Column` with selectable `uriwd.Text`s. Because of
       `urwid.Text`, the sizing mode of this widget is `flow` type.

    2. Original data provided are saved, even some of them may not be used in rendering. Then when
       we want to adjust the columns being rendered, we don't have to create new instances.

    3. Because of the `urwid.Text`, users have to make sure the data can be converted to `str`.

    4. If the key `"attachment path"` is provided in `data`, and its value is a list of
       paths/strings:

        a. If length of this list >= 2, when key in "enter", a window pops up and allows users to
           choose which attachment to open.
        b. If length of this list == 1, when key in "enter", the attachment will be opened with
           `xdg-open`
        c. If it is an empty list, nothing happens.

    5. If the value to `"attachment path"` is a single str/path, then it's the same as providing a
       length-one list.

    6. To enable the attachment selection pop-up, the major render loop `urwid.MainLoop` should
       have the `pop_ups` argument enabled.

    7. Color palette:
        a. Set `"normal doc"` for a widget not on focus; alternatively, set this widget's attribute
           `_normal_ctag` to change the tag from `"normal doc"` to another tag.
        b. Set `"selected doc"` for a widget on focus; alternatively, set this widget's attribute
           `_focus_ctag` to change the tag from `"selected doc"` to another tag.

    Examples
    --------
    >>> from urwid import MainLoop, ListBox, SimpleFocusListWalker
    >>> from totero.document import DocumentItem
    >>> item1 = {
            "author": "Abc et al.",
            "year": 2020,
            "title": "An example document 1",
            "publication": "Journal of Examples",
            "attachment path": ["~/example1.pdf", "~/example2.pdf"]
        }
    >>> item2 = {
            "author": "Def et al.",
            "year": 2019,
            "title": "An example document 2",
            "publication": "Journal of Examples",
            "attachment path": ["~/example3.pdf", "~/example4.pdf"]
        }
    >>> doc1 = DocumentItem(item1, ["author", "title", "publication", "year"], [20, 100, 30, 6])
    >>> doc2 = DocumentItem(item2, ["author", "title", "publication", "year"], [20, 100, 30, 6])
    >>> colors = [
            ("normal doc", "white", "black", None, None, None),
            ("selected doc", "black", "yellow", None, None, None),
            ("normal button", "white", "black", None, None, None),
            ("selected button", "black", "yellow", None, None, None),
            ("button outline", "white", "black", None, None, None),
            ("attachment win title", "light red,bold,italics", "black", None, None, None),
        ]
    >>> loop = MainLoop(ListBox(SimpleFocusListWalker([doc1, doc2])), colors, pop_ups=True)
    >>> loop.run()

    Use the arrow keys (up & down, or any custom keys that map to up and down) to select a different
    document and "enter" to open the attachment selection pop-up.
    """

    # color tag
    _normal_ctag = "normal doc"
    _focus_ctag = "selected doc"

    def __init__(
        self,
        data: _Union[_Mapping[str, _Any], _Series],
        columns: _Optional[_Sequence[str]] = None,
        weights: _Optional[_Sequence[int]] = None,
        wrap: _Optional[str] = "clip",
    ):
        # initialize parent with a placeholde/fake widget
        super().__init__(_Text(""), self._normal_ctag, self._focus_ctag)

        # if pandas.Series is provided, convert it to `dict`
        if isinstance(data, _Series):
            data = data.to_dict()
        elif not isinstance(data, dict):
            raise ValueError("Neither a `dict` nor a `pandas.Series`: {}".format(type(data)))

        # attachment widgets
        try:
            if not isinstance(data["attachment path"], (list, tuple)):
                self._attachments = [_AttachmetnItem(data.pop("attachment path"))]
            else:
                self._attachments = [_AttachmetnItem(p) for p in data.pop("attachment path")]
        except KeyError:  # attachment path does not exist
            self._attachments = []

        # initial attachment windows status
        self._attachment_win = None

        # convert data to a dict of urwid.Text
        self._data = {key: _Text(str(value), wrap=wrap) for key, value in data.items()}

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

    def keypress(self, size: _Sequence[int], key: str):
        """See the docstring of urwid.Widget.keypress."""
        if key == "enter":
            if len(self._attachments) == 0:
                return None

            if len(self._attachments) == 1:
                return self._attachments[0].keypress(size, key)

            self._attachment_win = [_AttachmentSelectionPopUP(self._attachments)]
            self._attachment_win.extend([1, 1, 100, len(self._attachments)+5])
            _connect_signal(self._attachment_win[0], "close", self._clear_pop_up)
            self._invalidate()
            return None

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
            self._columns = list(self._data.keys())
        else:  # make sure users did not request to show "attachment path"
            if "attachment path" in columns:
                raise ValueError("\"attachment path\" is not allowed in visible columns.")
            self._columns = _deepcopy(columns)

        # if no weights provided, use equal widths
        if weights is None:
            self._weights = [1] * len(self._columns)
        else:
            self._weights = _deepcopy(weights)

        # underlying widget; a urwid.Column; will be saved as self._original_widget after __init__
        cols = [("weight", w, self._data[k]) for w, k in zip(self._weights, self._columns)]
        cols = _Columns(cols, dividechars=1)
        cols.ignore_focus = False
        cols._selectable = True

        # reset and rerender
        self._set_original_widget(cols)

    def _clear_pop_up(self, event: _Any):  # pylint: disable=unused-argument
        """Remove the pop-up attachment selection window.

        Parameters
        ----------
        event : any
            Not used here. Just for compatibility with other signal callbacks.
        """
        self._attachment_win = None
        self._invalidate()
