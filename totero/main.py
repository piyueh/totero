#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Pi-Yueh Chuang <pychuang@pm.me>
#
# Distributed under terms of the BSD 3-Clause license.

"""Main function of the TUI client."""
import argparse
import urwid
import zoteroutils
from .documentlist import DocumentList
from .misc import exit_trigger, default_theme


def get_cmd_args():
    """Returns CMD arguments throught argparse module.

    Returns
    -------
    argparse.Namespace
        Returned by argparse.ArgumentParser().parse_args()
    """

    parser = argparse.ArgumentParser(
        prog="totero",
        description="TUI client for Zotero's local SQLite database",
        epilog="Website: https://github.com/piyueh/totero"
    )
    parser.add_argument("path", help="The path to Zotero's folder.", metavar="PATH")

    args = parser.parse_args()
    return args


def main():
    """Main function of the TUI client."""

    zpath = get_cmd_args().path
    db = zoteroutils.Database(zpath)
    docs = db.get_all_docs()

    columns = ["author", "year", "title", "publication title", "time added"]
    weights = [20, 6, 100, 40, 20]
    box = urwid.LineBox(urwid.Padding(DocumentList(docs, columns, weights), left=2, right=2))

    loop = urwid.MainLoop(box, default_theme, unhandled_input=exit_trigger, pop_ups=True)
    loop.run()
