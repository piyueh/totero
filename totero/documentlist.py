#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Pi-Yueh Chuang <pychuang@pm.me>
#
# Distributed under terms of the BSD 3-Clause license.

"""A window showing a list of documents."""
from copy import deepcopy as _deepcopy
from typing import Union as _Union
from typing import Optional as _Optional
from typing import Sequence as _Sequence
from pandas import DataFrame as _DataFrame
from urwid import SimpleFocusListWalker as _SimpleFocusListWalker
from urwid import Text as _Text
from urwid import Pile as _Pile
from urwid import Filler as _Filler
from urwid import ListBox as _ListBox
from urwid import AttrMap as _AttrMap
from urwid import Columns as _Columns
from urwid import Divider as _Divider
from urwid import CompositeCanvas as _CompositeCanvas
from urwid import connect_signal as _connect_signal
from .document import DocumentItem as _DocumentItem
from .optionlist import OptionList as _OptionList


class DocumentList(_AttrMap):
    """A window showing a list of documents.

    Items in the list are selectable. "enter" on a item will open an attachment with `xdg-open`,
    if the item has attachments.

    Parameters
    ----------
    data : pandas.DataFrame
        The raw data of a document list with brief info. The `pandas.DataFrame` should have at least
        the columns requested by `columns`. This widget makes a deep copy of the `data`.
    columns : list of str, or None
        The columns to be shown when rendered. The keys in `columns` should be valid column names of
        the `data`. If `None`, use all columns from `data`.
    weights : list of int, or None
        The weights of the column widths. If None, use the columns' average lenghts in `data`. If
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

        # initialize widgets
        self._content = _ListBox(_SimpleFocusListWalker([]))
        self._header = _AttrMap(_Columns([], dividechars=2), self._header_ctag)

        super().__init__(
            _Pile([
                (1, _Filler(self._header)),
                (1, _Filler(_AttrMap(_Divider("-"), self._divider_ctag))),
                self._content
            ]), None
        )

        # initialize attributes
        self._wrap = wrap
        self._columns = None
        self._weights = None
        self._data = None

        # set the data and adjust the displated columns
        self.reset_data(data)
        self.reset_columns(columns, weights)

        # initialize pop up windows
        self._sort_selection_win = None

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
            self._columns.remove("widget")
        else:
            self._columns = _deepcopy(columns)

        # if no weights provided, use columns' average lendth
        if weights is None:
            self._weights = self._data[self._columns].applymap(str).applymap(len)
            self._weights = (self._weights.median(0) + 0.5).astype(int).tolist()
        else:
            self._weights = _deepcopy(weights)

        # configure the header
        self._header.original_widget.contents = [
            (_Text(c, wrap=self._wrap), ("weight", w, False))
            for w, c in zip(self._weights, self._columns)
        ]

        # a Series of DocumentItem
        for widget in self._data["widget"]:
            widget.reset_columns(self._columns, self._weights)

    def reset_data(self, data: _DataFrame):
        """Reset the underlying pandas.DataFrame.

        Parameters
        ----------
        data : pandas.DataFrame
        """
        _c, _w, _wrap = self._columns, self._weights, self._wrap  # to make code shorter
        self._data = data.copy()
        self._data["widget"] = self._data.apply(lambda x: _DocumentItem(x, _c, _w, _wrap), 1)
        self._content.body.clear()
        self._content.body.extend(self._data["widget"])
        self._content.body.set_focus(0)

    def sort_by(self, columns: _Union[str, _Sequence[str]], ascending: bool = True):
        """Sort the document list based on the values in a column.

        Parameters
        ----------
        column : str or list or str
            The column(s) used for sorting.
        ascending : bool
            Ascending or descending.
        """

        self._data = self._data.sort_values(columns, 0, ascending)
        self._content.body.clear()
        self._content.body.extend(self._data["widget"])
        self._content.body.set_focus(0)

    def render(self, size: _Sequence[int], focus: bool = False):
        """See the docstring of urwid.Widget.render."""
        canv = super().render(size, focus)
        if self._sort_selection_win is not None:
            canv = _CompositeCanvas(canv)
            width = min(max(26, max(map(lambda x: len(x)+8, self._columns))), canv.cols()-2)
            height = min(len(self._columns)+5, canv.rows()-2)
            left = (canv.cols() - width) // 2
            top = (canv.rows() - height) // 2
            canv.set_pop_up(self._sort_selection_win, left, top, width, height)
        return canv

    def keypress(self, size: _Sequence[int], key: str):  # pylint: disable=unused-argument
        """See the docstring of urwid.Widget.keypress."""
        if self._command_map[key] == "sort documents":
            self._trigger_sort()
            return None
        return super().keypress(size, key)

    def _trigger_sort(self):
        """Create popup to ask what columns should be used for sorting."""

        def finalize_popup(event):  # pylint: disable=unused-argument
            keys = self._sort_selection_win.selected
            self._sort_selection_win = None
            self._invalidate()
            try:
                self.sort_by(keys)
            except IndexError:  # no keys returned
                pass

        self._sort_selection_win = _OptionList(self._columns, title="Select solumns to sort")
        _connect_signal(self._sort_selection_win, "close", finalize_popup)
        self._invalidate()
