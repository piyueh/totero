totero -- a TUI client for Zotero 
=================================

-----------------------------------------------------------------------------

**Note**:
I don't have enough time to work on this, though I haven't completely given
this project up. Any contribution or/and collaboration are welcome!

-----------------------------------------------------------------------------

***totero*** is a TUI (text/terminal-based user interfaces) client for Zotero
that relies only on local database (i.e., no need for a cloud Zotero account).
The official Zotero GUI client is bundled with an old-version FireFox, which
does not support Wayland. Under a Wayland environment, the official Zotero
client must rely on XWayland and does not look nice, especially with 4K and
HiDPI monitors. So I decided to make my own client.

TUI clients usually looks nice because most modern terminal emulators support
256 colors or even 24-bit true colors. Here's a showcase of this
client in Sway WM:

![totero_demo](https://pychao.com/wp-content/uploads/2020/11/totero_demo.gif)

## Installation
---------------
This is a WIP. No `pip` or `conda` packages.

Dependencies:

* `python` >= 3.7
* `zoteroutils`: https://github.com/piyueh/zoteroutils
* `pandas`
* `sqlalchemy `(required by `zoteroutils`)
* `urwid`

`pandas`, `sqlalchemy` and `urwid` can be installed through whatever package
managers preferred. `zoteroutils` is a companion package of `totero`, so it's
also a WIP and has to be downloaded manually:

```
$ git clone https://github.com/piyueh/zoteroutils
```

Let `python` know where to find `zoteroutils`:

```
$ export PYTHONPATH=<path to the zoteroutils>:${PYTHONPATH}
```

Then download this client:

```
$ git clone https://github.com/piyueh/totero
```

Finally, run the client:

```
$ python <path to totero>/totero.py <path to Zotero data folder>
```

## Features
-----------

1. Pure Python -- easy to read and modified the code
2. Using `xdg-open` to open attachments by `enter`. Poping up a window to choose
   an attachment if multiple files exists for the selected document.
3. Sorting with `F1` key. Poping up a window to choose which column(s) to sort.
4. Selecting displayed columns with `F2` key. Poping up a window to choose column(s).
4. Moving with `h`, `j`, `k`, and `l` keys
5. Customizable color themes and key mappings. 

## TODO
-------

These features are under development:

1. Selecting a collection and showing documents in this collection
2. Poping up a window to show the detail information of a selected document
3. Searching
4. A toolbar and a status bar
5. Exporting to a bibtex file or a clipboard.

The following features are in the plan but probably won't be finished in the near
future:

1. Anything related to writing into the SQLite database. One reason is that I'm
   not familiar with SQL. Another reason is that I may not have time.
