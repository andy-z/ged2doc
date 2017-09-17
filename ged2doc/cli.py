# -*- coding: utf-8 -*-

"""Console script for ged2doc."""

from __future__ import absolute_import, division, print_function

from argparse import ArgumentParser

from ged2doc.size import String2Size
from ged2doc.input import make_file_locator
from ged2doc.html_writer import HtmlWriter


def main():
    """Console script for ged2doc."""

    parser = ArgumentParser(description='Convert GEDCOM file into document.')
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
    group.add_argument("--encoding-errors", default="strict",
                       help="Mode for handling decoding errors, one of strict,"
                       " ignore, or replace; default: %(default)s")

    group = parser.add_argument_group("Output Options")
    group.add_argument('-t', "--type", default='html',
                       help=("Type of the output document, possible values:"
                             " html, odt; default: %(default)s"))
    group.add_argument('-d', "--date-format", default=None, metavar="FMT",
                       help="Date format in output document, one of "
                       "DMY., YMD-, MDY/; if missing then use system default")

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

    # instantiate file locator
    try:
        flocator = make_file_locator(args.input, args.file_name_pattern,
                                     args.image_path)
    except Exception as exc:
        parser.error("Error reading input file: {0}".format(exc))

    if args.type == "html":
        options = dict(
            html_page_width=args.html_page_width,
            html_image_width=args.html_image_width,
            html_image_height=args.html_image_height,
            html_image_upscale=args.html_image_upscale,
            encoding=args.encoding,
            encoding_errors=args.encoding_errors,
            )
        writer = HtmlWriter(flocator, options)

    try:
        writer.save(args.output)
    except Exception as exc:
        parser.error("Error while producing a document: {0}".format(exc))
