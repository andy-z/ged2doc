#!/usr/bin/env python

'''Python module for generating EMF.

Only the most trivial features are implemented, stuff that is required by
ged2doc package.
'''

import struct

from ged2doc import dumbemf


def main():
    """Simple command line utility to parse/dump EMF"""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=argparse.FileType("rb"))
    parser.add_argument("-v", dest="verbose", action="store_true", default=False,
                        help="verbose output")
    args = parser.parse_args()

    data = args.file.read(8)
    while data:

        rectype, size = struct.unpack("II", data)
        for name, value in vars(dumbemf).items():
            if name.startswith("EMR_") and value == rectype:
                rectype = name
        print("{} size={}".format(rectype, size))

        # read remaining data
        data += args.file.read(size - 8)
        if args.verbose:
            offset = 0
            while data:
                line, data = data[:16], data[16:]
                fline = "    {:03d}:".format(offset)
                bline = list(line)
                bline += [None] * (16 - len(bline))

                for i, b in enumerate(bline):
                    if i % 4 == 0:
                        fline += "  "
                    if b is not None:
                        fline += " {:02X}".format(b)
                    else:
                        fline += "   "

                for i, b in enumerate(bline):
                    if i % 4 == 0:
                        fline += "  "
                    if b is None:
                        fline += "  "
                    elif 32 <= b < 127:
                        fline += " {}".format(chr(b))
                    else:
                        fline += " ."

                for i in (0, 4, 8, 12):
                    if i < len(line):
                        v, = struct.unpack("I", line[i:i+4])
                        fline += " {:010d}".format(v)

                print(fline)
                offset += 16

        # next record, if any
        data = args.file.read(8)


if __name__ == "__main__":
    main()
