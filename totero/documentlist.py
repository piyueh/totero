#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Pi-Yueh Chuang <pychuang@pm.me>
#
# Distributed under terms of the BSD 3-Clause license.

"""A window showing a list of documents."""
from copy import deepcopy as _deepcopy
from typing import Optional as _Optional
from typing import Sequence as _Sequence
from pandas import DataFrame as _DataFrame
from urwid import SimpleFocusListWalker as _SimpleFocusListWalker
from urwid import Text as _Text
from urwid import ListBox as _ListBox
from urwid import AttrMap as _AttrMap
from urwid import Columns as _Columns
from urwid import Divider as _Divider
from .document import DocumentItem as _DocumentItem


class DocumentList(_AttrMap):
    """A window showing a list of documents.

    Items in the list are selectable. "enter" on a item will open an attachment with `xdg-open`,
    if the item has attachments.

    Parameters
    ----------
    data : pandas.DataFrame
        The raw data of a document list with brief info. The `pandas.DataFrame` should have at least
        the columns requested by `columns`. This widget makes a reference to the `data` so simple.
    columns : list of str, or None
        The columns to be shown when rendered. The keys in `columns` should be valid column names of
        the `data`. If `None`, use all columns from `data`.
    weights : list of int, or None
        The weights of the column widths. If None, assume all column widths are the same. If
        `weights` is provided, it should have the same langth as the `columns`.
    wrap : str
        The `wrap` argument in a `urwid.Text` widget. Whether the texts insides columns should be
        wrapped if longer than the column widths.

    Notes
    -----
    To enable the attachment selection pop-up, the major render loop `urwid.MainLoop` should have
    the `pop_ups` argument enabled.

    Color palette
    -------------
    1. Set `"doc list header"` for the header; alternatively, set this class' attribute
       `_header_ctag` to change the tag name.
    2. Set `"doc list divider"` for the divider between the header and the list; alternatively, set
       this class' attribute `_divider_ctag` to change the tag name.

    Examples
    --------
    >>> from pandas import DataFrame
    >>> from urwid import MainLoop
    >>> from totero import DocumentList
    >>> df = DataFrame({
            "author": ["Abc et al.", "Def et al."],
            "year": [2020, 2019],
            "title": ["An example document 1", "An example document 2"],
            "publication": ["Journal of Examples", "Journal of Examples"],
            "attachment path": ["~/example1.pdf", ["~/example2.pdf", "~/example3.pdf"]]
        })
    >>> colors = [
            ("doc item normal", "white", "black"), ("doc item focus", "black", "yellow"),
            ("atthmnt win title", "light red,bold,italics", "black"),
            ("atthmnt item normal", "white", "black"), ("atthmnt item focus", "black", "yellow"),
            ("cncl butn normal", "white", "black"), ("cncl butn focus", "black", "yellow"),
        ]
    >>> loop = MainLoop(DocumentList(df), colors, pop_ups=True)
    >>> loop.run()

    Use the arrow keys (up & down, or any custom keys that map to up and down) to select a different
    document and "enter" to open the attachment selection pop-up.
    """

    _header_ctag = "doc list header"
    _divider_ctag = "doc list divider"

    def __init__(
        self, data: _DataFrame, columns: _Optional[_Sequence[str]] = None,
        weights: _Optional[_Sequence[int]] = None, wrap: str = "clip",
    ):
        # sanity check
        assert isinstance(data, _DataFrame), "`data` should be a pandas.DataFrame."

        super().__init__(_ListBox(_SimpleFocusListWalker([])), None)
        self.original_widget.body.append(_AttrMap(_Columns([], dividechars=1), self._header_ctag))
        self.original_widget.body.append(_AttrMap(_Divider("="), self._divider_ctag))

        # a strong reference to the provided data
        self._data = data

        # initialize document item list
        self._docs = self._data.apply(lambda x: _DocumentItem(x, None, None, wrap), 1)

        # set the list
        self.original_widget.body.extend(self._docs)
        self.original_widget.body.set_focus(0)

        # initial options
        self._wrap = wrap
        self._columns = None
        self._weights = None

        # adjust the displayed columns
        self.reset_columns(columns, weights)

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
            self._columns = self._data.columns.to_list()
        else:
            self._columns = _deepcopy(columns)

        # if no weights provided, use equal widths
        if weights is None:
            self._weights = [1] * len(self._columns)
        else:
            self._weights = _deepcopy(weights)

        # configure the header
        self.original_widget.body[0].original_widget.contents = [
            (_Text(c, wrap=self._wrap), ("weight", w, False))
            for w, c in zip(self._weights, self._columns)
        ]

        # a Series of DocumentItem
        for widget in self._docs:
            widget.reset_columns(self._columns, self._weights)

    def reset_data(self, data: _DataFrame):
        """Reset the underlying pandas.DataFrame."""
        _c, _w, _wrap = self._columns, self._weights, self._wrap  # to make code shorter
        self._data = data
        self._docs = self._data.apply(lambda x: _DocumentItem(x, _c, _w, _wrap), 1)

        # will re-use the header and divider
        header, divider = self.original_widget.body[:2]

        self.original_widget.body.clear()
        self.original_widget.body.append(header)
        self.original_widget.body.append(divider)
        self.original_widget.body.extend(self._docs)
        self.original_widget.body.set_focus(0)