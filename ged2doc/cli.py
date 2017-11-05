# -*- coding: utf-8 -*-

"""Console script for ged2doc."""

from __future__ import absolute_import, division, print_function

from argparse import ArgumentParser
import locale
import logging

from .size import String2Size
from .i18n import I18N
from .input import make_file_locator
from .html_writer import HtmlWriter


_log = logging.getLogger(__name__)


languages = ['en', 'ru']


def _system_lang():
    """Try to guess system language
    """
    loclang, _ = locale.getdefaultlocale()
    for lang in languages:
        if loclang.startswith(lang):
            return lang
    return "en"


def main():
    """Console script for ged2doc."""

    parser = ArgumentParser(description='Convert GEDCOM file into document.')
    parser.add_argument('-v', "--verbose", action="count", default=0,
                        help="Print some info to standard output, "
                        "-vv prints debug info.")
    parser.add_argument("input",
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
    group.add_argument('-t', "--type", default='html',
                       help=("Type of the output document, possible values:"
                             " html, odt; default: %(default)s"))
    group.add_argument('-l', "--language", default=_system_lang(),
                       metavar="LANG_CODE", choices=languages,
                       help="Language for output document, supported "
                       "languages are: %(choices)s. Default is to use "
                       "system  language (=%(default)s).")
    group.add_argument('-d', "--date-format", default=None, metavar="FMT",
                       help="Date format in output document, one of "
                       "DMY., YMD-, MDY/; if missing then use system default")
    group.add_argument("--no-toc", default=False, action="store_true",
                       help="Disable Table of Contents in output document.")
    group.add_argument("--no-stat", default=False, action="store_true",
                       help="Disable Name Statistics in output document.")

    group = parser.add_argument_group("HTML Output Options")
    group.add_argument("--html-page-width", default="800px",
                       metavar="SIZE", type=String2Size("px"),
                       help="HTML page width in pixels; default: %(default)s")
    group.add_argument("--html-image-width", default="300px",
                       metavar="SIZE", type=String2Size("px"),
                       help="image width in pixels; default: %(default)s")
    group.add_argument("--html-image-height", default="300px",
                       metavar="SIZE", type=String2Size("px"),
                       help="image height in pixels; default: %(default)s")
    group.add_argument('-u', "--html-image-upscale", default=False,
                       action="store_true", help="Upscale small images")

    args = parser.parse_args()

    if args.verbose == 0:
        log_level = logging.WARN
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    logfmt = "%(levelname)s: %(name)s (%(filename)s:%(lineno)d)"\
             " -- %(message)s"
    logging.basicConfig(level=log_level, format=logfmt)

    # instantiate file locator
    try:
        flocator = make_file_locator(args.input, args.file_name_pattern,
                                     args.image_path)
    except Exception as exc:
        parser.error("Error reading input file: {0}".format(exc))

    tr = I18N(args.language, args.date_format)

    if args.type == "html":
        options = dict(
            html_page_width=args.html_page_width,
            html_image_width=args.html_image_width,
            html_image_height=args.html_image_height,
            html_image_upscale=args.html_image_upscale,
            encoding=args.encoding,
            encoding_errors=args.encoding_errors,
            make_toc=not args.no_toc,
            make_stat=not args.no_stat,
            )
        writer = HtmlWriter(flocator, options, tr)

    try:
        writer.save(args.output)
    except Exception as exc:
        _log.error("caught exception: %s", exc, exc_info=True)
        _log.error("Error while producing a document: {0}".format(exc))
