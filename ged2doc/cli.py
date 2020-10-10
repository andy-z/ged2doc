# -*- coding: utf-8 -*-

"""Console script for ged2doc."""

from argparse import ArgumentParser, FileType
import locale
import logging
import os
import platform
import sys

from .size import String2Size
from .i18n import I18N, DATE_FORMATS
from .input import make_file_locator
from .html_writer import HtmlWriter
from .name import NameFormat
from .odt_writer import OdtWriter
from .utils import languages, system_lang
import ged2doc
import ged4py
from ged4py.model import NameOrder

_log = logging.getLogger(__name__)


NAME_ORDER_LIST = [item.value for item in NameOrder]


def _make_writer(args=None):
    """Make Writer instance based on command line arguments.

    Parameters
    ----------
    args : `list` [ `str` ]
        List of command line arguments passed to argparse, optional, by
        default uses `sys.argv`.

    Returns
    -------
    args : `argparse.Namespace`
        Parsed command line arguments.
    writer : `ged2doc.writer.Writer`
        Instance of `~ged2doc.writer.Writer` to use for writing output file.
    """

    version = "ged2doc {0} (ged4py {1}; python {2})".format(ged2doc.__version__,
                                                            ged4py.__version__,
                                                            platform.python_version())

    parser = ArgumentParser(description='Convert GEDCOM file into document.')
    parser.add_argument('-v', "--verbose", action="count", default=0,
                        help="Print some info to standard output, "
                        "-vv prints debug info.")
    parser.add_argument("--log", default=None, metavar="PATH",
                        type=FileType(mode="wt"),
                        help="Produces log file with debugging information.")
    parser.add_argument("--version", action="version", version=version,
                        help="Print version information and exit")
    # TODO: can enable FileType when Python2 support is dropped
    parser.add_argument("input",  # type=FileType(mode="rb",),
                        help="Location of input file, input file can be "
                        "either GEDCOM file or ZIP archive which can also "
                        "include images.")
    parser.add_argument("output", help="Location of output file.")

    group = parser.add_argument_group("Input Options")
    group.add_argument('-i', "--image-path", metavar="PATH",
                       help="Directory containing files with images")
    group.add_argument('-p', "--file-name-pattern", metavar="PATTERN",
                       default="*.ged*",
                       help="Pattern to search for GEDCOM file inside ZIP "
                       "archive, default: %(default)s")
    group.add_argument("--encoding",
                       help="Input file encoding, default is to guess "
                       "from file contents")
    group.add_argument("--encoding-errors", default="strict", metavar="MODE",
                       help="Mode for handling decoding errors, one of strict,"
                       " ignore, or replace; default: %(default)s")

    group = parser.add_argument_group("Output Options")
    group.add_argument('-t', "--type", default=None, choices=['html', 'odt'],
                       help=("Type of the output document, possible values:"
                             " %(choices)s; by default type is determined by"
                             " output file extension (*.odt, *.html, or *.htm"
                             " are recognized)"))
    group.add_argument('-l', "--language", default=system_lang(),
                       metavar="LANG_CODE", choices=languages(),
                       help="Language for output document, supported "
                       "languages are: %(choices)s. Default is to use "
                       "system  language (=%(default)s).")
    group.add_argument('-d', "--date-format", default=None, metavar="FMT",
                       choices=DATE_FORMATS,
                       help="Date format in output document, one of "
                       "%(choices)s; if missing then language-specific "
                       "format is used.")
    group.add_argument('-s', "--sort-order", default=NameOrder.SURNAME_GIVEN.value,
                       metavar="ORDER", choices=NAME_ORDER_LIST,
                       help="Ordering of the individuals, one of "
                       "%(choices)s; default: %(default)s.")
    group.add_argument("--locale", default=None, metavar="LOCALE",
                       help=("Locale name to use for name ordering, "
                             "default is to use system locale."))
    group.add_argument("--no-missing-date", default=False, action="store_true",
                       help="Do not output events if they have no dates.")
    group.add_argument("--no-image", default=False, action="store_true",
                       help="Disable images in output document.")
    group.add_argument("--no-toc", default=False, action="store_true",
                       help="Disable Table of Contents in output document.")
    group.add_argument("--no-stat", default=False, action="store_true",
                       help="Disable Name Statistics in output document.")
    group.add_argument('-w', "--tree-width", default=4, type=int,
                       metavar="NUMBER",
                       help="Number of generations in ancestors tree, "
                       "default: %(default)s")

    group = parser.add_argument_group("Name Format Options")
    group.add_argument("--name-surname-first", dest='name_fmt',
                       action='append_const', const=NameFormat.SURNAME_FIRST,
                       help="Format names with surname in leading position.")
    group.add_argument("--name-comma", dest='name_fmt',
                       action='append_const', const=NameFormat.COMMA,
                       help="Format names with surname followed by comma "
                       "(only if surname is in leading position).")
    group.add_argument("--name-maiden", dest='name_fmt',
                       action='append_const', const=NameFormat.MAIDEN,
                       help="Format names with surname followed by maiden "
                       "name in parentheses.")
    group.add_argument("--name-maiden-only", dest='name_fmt',
                       action='append_const', const=NameFormat.MAIDEN_ONLY,
                       help="Format names with maiden name for surname.")
    group.add_argument("--name-capital", dest='name_fmt',
                       action='append_const', const=NameFormat.CAPITAL,
                       help="Format names with surname and maiden name in "
                       "all capital.")

    group = parser.add_argument_group("HTML Output Options")
    group.add_argument("--html-page-width", default="800px",
                       metavar="SIZE", type=String2Size("px"),
                       help="HTML page width in pixels; default: %(default)s")
    group.add_argument("--html-image-width", default="300px",
                       metavar="SIZE", type=String2Size("px"),
                       help="Image width in pixels; default: %(default)s")
    group.add_argument("--html-image-height", default="300px",
                       metavar="SIZE", type=String2Size("px"),
                       help="Image height in pixels; default: %(default)s")
    group.add_argument('-u', "--html-image-upscale", default=False,
                       action="store_true", help="Upscale small images")

    group = parser.add_argument_group("ODT Output Options")
    group.add_argument("--odt-page-width", default="6in",
                       metavar="SIZE", type=String2Size("in"),
                       help="ODT page width in inches; default: %(default)s")
    group.add_argument("--odt-page-height", default="9in",
                       metavar="SIZE", type=String2Size("in"),
                       help="ODT page height in inches; default: %(default)s")
    group.add_argument("--odt-margin-left", default="0.5in",
                       metavar="SIZE", type=String2Size("in"),
                       help="Page left margin in inches; default: %(default)s")
    group.add_argument("--odt-margin-right", default="0.5in",
                       metavar="SIZE", type=String2Size("in"),
                       help="Page right margin in inches; "
                       "default: %(default)s")
    group.add_argument("--odt-margin-top", default="0.5in",
                       metavar="SIZE", type=String2Size("in"),
                       help="Page top margin in inches; default: %(default)s")
    group.add_argument("--odt-margin-bottom", default="0.25in",
                       metavar="SIZE", type=String2Size("in"),
                       help="Page bottom margin in inches; "
                       "default: %(default)s")
    group.add_argument("--odt-image-width", default="2in",
                       metavar="SIZE", type=String2Size("in"),
                       help="Image width in inches; default: %(default)s")
    group.add_argument("--odt-image-height", default="2in",
                       metavar="SIZE", type=String2Size("in"),
                       help="Image height in inches; default: %(default)s")
    group.add_argument("--first-page", default=1,
                       metavar="NUMBER", type=int,
                       help="Number of the first page; default: %(default)s")
    group.add_argument("--odt-tree-type", choices=["emf", "svg"], default="emf",
                       metavar="FORMAT",
                       help="Type of image format for ancestor tree, one of "
                       "%(choices)s; default: %(default)s")

    args = parser.parse_args(args)

    # configure logging
    if args.verbose == 0:
        log_level = logging.WARN
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setLevel(log_level)
    handlers = [handler]
    if args.log:
        # this will log all levels (NOTSET is default)
        handler = logging.StreamHandler(stream=args.log)
        handlers += [handler]
    # rot logger will pass all messages, handlers will filter them
    logfmt = "%(levelname)s: %(name)s (%(filename)s:%(lineno)d)"\
             " -- %(message)s"
    logging.basicConfig(level=logging.NOTSET, format=logfmt, handlers=handlers)

    # some debugging info
    _log.debug("version: %s", version)
    _log.debug("args: %s", args)

    # set locale
    if args.locale:
        locale.setlocale(locale.LC_ALL, args.locale)
    else:
        locale.setlocale(locale.LC_ALL, '')
    _log.debug("LC_ALL: %s", locale.setlocale(locale.LC_ALL))
    _log.debug("LC_COLLATE: %s", locale.setlocale(locale.LC_COLLATE))

    # instantiate file locator
    try:
        flocator = make_file_locator(args.input, args.file_name_pattern,
                                     args.image_path)
    except Exception as exc:
        _log.debug("caught exception: %s", exc, exc_info=True)
        parser.error("Error reading input file: {0}".format(exc))

    tr = I18N(args.language, args.date_format)

    name_fmt = NameFormat(0)
    for option in args.name_fmt or []:
        name_fmt |= option

    # guess output type if not set
    if args.type is None:
        ext = os.path.splitext(args.output)[1]
        if ext.lower() == ".odt":
            args.type = "odt"
        elif ext.lower() in (".htm", ".html"):
            args.type = "html"
        else:
            parser.error("Cannot determine document type from file extension,"
                         " use --type option to specify document type")

    _log.debug("args: %s", args)

    if args.type == "html":
        writer = HtmlWriter(flocator, args.output, tr,
                            encoding=args.encoding,
                            encoding_errors=args.encoding_errors,
                            sort_order=NameOrder(args.sort_order),
                            name_fmt=name_fmt,
                            events_without_dates=not args.no_missing_date,
                            make_toc=not args.no_toc,
                            make_stat=not args.no_stat,
                            make_images=not args.no_image,
                            tree_width=args.tree_width,
                            page_width=args.html_page_width,
                            image_width=args.html_image_width,
                            image_height=args.html_image_height,
                            image_upscale=args.html_image_upscale)
    elif args.type == "odt":
        writer = OdtWriter(flocator, args.output, tr,
                           encoding=args.encoding,
                           encoding_errors=args.encoding_errors,
                           sort_order=NameOrder(args.sort_order),
                           events_without_dates=not args.no_missing_date,
                           make_toc=not args.no_toc,
                           make_stat=not args.no_stat,
                           make_images=not args.no_image,
                           tree_width=args.tree_width,
                           name_fmt=name_fmt,
                           page_width=args.odt_page_width,
                           page_height=args.odt_page_height,
                           margin_left=args.odt_margin_left,
                           margin_right=args.odt_margin_right,
                           margin_top=args.odt_margin_top,
                           margin_bottom=args.odt_margin_bottom,
                           image_width=args.odt_image_width,
                           image_height=args.odt_image_height,
                           first_page=args.first_page,
                           tree_format=args.odt_tree_type)

    return args, writer


def main(args=None):
    """Console script for ged2doc.

    Parameters
    ----------
    args : `list` [ `str` ], optional
        Command line arguments, be default ``sys.argv`` is used.
    """

    args, writer = _make_writer(args)

    try:
        writer.save()
        _log.debug("Success")
        return 0
    except Exception as exc:
        _log.debug("caught exception: %s", exc, exc_info=True)
        print("Error while producing a document:\n  {}".format(exc),
              file=sys.stderr)
        # clear output file in case some partial output was written
        try:
            _log.debug("trying to remove output file: %s", args.output)
            os.unlink(args.output)
        except OSError as exc:
            _log.debug("caught exception while removing file: %s", exc)
        return 1
