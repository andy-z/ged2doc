.. |ged2doc| replace:: ``ged2doc``


Usage
=====

|ged2doc| package can be used either as a standalone application (command line
tool) with the same name |ged2doc| or as a Python library/package that can be
imported by other Python code. |ged2doc| main function is to parse GEDCOM data
and convert it into printable/browsable document format. For GEDCOM parsing
|ged2doc| uses `ged4py`_ package, if you only need to parse GEDCOM file from
Python code and do not need to produce output document then `ged4py`_ package
is a good place to start.

.. _ged4py: https://ged4py.readthedocs.io/

Command line tool
-----------------

|ged2doc| application is the main user interface, it reads and parses GEDCOM
file and produces document in one of the supported formats (currently HTML and
OpenDocument Text/OTD).

|ged2doc| application is a command line tool which is run from a terminal, it
has a large number of command line options which control contents and
appearance of the produced output document. To get a brief description of all
options run the command with ``--help`` or ``-h`` option::

    % ged2doc --help
    usage: ged2doc [-h] [-v] [--log PATH] [--version] [-i PATH] [-p PATTERN]
                [--encoding ENCODING] [--encoding-errors MODE] [-t {html,odt}]
                [-l LANG_CODE] [-d FMT] [-s ORDER] [--locale LOCALE]
                [--no-missing-date] [--no-image] [--no-toc] [--no-stat]
                [-w NUMBER] [--name-surname-first] [--name-comma]
                [--name-maiden] [--name-maiden-only] [--name-capital]
                [--html-page-width SIZE] [--html-image-width SIZE]
                [--html-image-height SIZE] [-u] [--odt-page-width SIZE]
                [--odt-page-height SIZE] [--odt-margin-left SIZE]
                [--odt-margin-right SIZE] [--odt-margin-top SIZE]
                [--odt-margin-bottom SIZE] [--odt-image-width SIZE]
                [--odt-image-height SIZE] [--first-page NUMBER]
                [--odt-tree-type FORMAT]
                input output

    Convert GEDCOM file into document.

    positional arguments:
      input                 Location of input file, input file can be either
                            GEDCOM file or ZIP archive which can also include
                            images.
      output                Location of output file.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Print some info to standard output, -vv prints debug
                            info.
      --log PATH            Produces log file with debugging information.
      --version             Print version information and exit

    ... description of all other options ...

Application takes two required positional arguments -- the name of input and
output files -- and a bunch of optional arguments. Sections below provide
more detailed description of the positional and optional arguments that this
command accepts. Optional arguments with value can be specified either as
``--option value`` or ``--option=value``.

Input files
^^^^^^^^^^^

First positional argument is an input file which can be either a GEDCOM file
or a ZIP archive. If ZIP archive is specified as an argument then it should
contain GEDCOM file and it may also contain image files referenced from GEDCOM
file. |ged2doc| can only process one GEDCOM file at a time even if ZIP
archive contains multiple GEDCOM files. Application tries to guess which file
in ZIP archive is a GEDCOM file based on pattern match, by default ``*.ged*``
pattern is used which matches names like ``file.ged`` or ``file.gedcom``.
File in archive can be located in any sub-folder, whole ZIP archive is
searched for matching files.

If GEDCOM file in archive has different extension or if there is more than
one file matching default pattern then option ``-p PATTERN``  should be used
to provide more exact match, e.g.::

    $ unzip -l archive.zip
      Length      Date    Time    Name
    ---------  ---------- -----   ----
            0  2017-10-30 22:28   folder1/
        77279  2017-10-30 22:28   folder1/file1.ged
            0  2017-10-30 22:28   folder2/
        79999  2017-10-30 22:28   folder2/file2.ged

    $ ged2doc -p file1.ged archive.zip output.html

GEDCOM file can contain references to images which can be included into
resulting document (in current implementation only one main image is included
per person). |ged2doc| tries to locate image file by first using unchanged
path directly from GEDCOM file (if the path is relative then it is resolved
relative to current working directory). If image file cannot be found and
``-i PATH`` is given then |ged2doc| tries to locate image using only base
name of the image path by recursively scanning ``PATH`` given in ``-i``
option. If input file is an archive then archive is searched for images first
using base name of the path from GEDCOM file, if image is not found in archive
then above logic is used to search for image on disk.

Output file
^^^^^^^^^^^

|ged2doc| saves output document in a file given as a second positional
argument. Currently |ged2doc| can generate either single-page HTML with
embedded images or OpenDocument Text (ODT) format. HTML format is better
suitable for online browsing as it includes navigation, ODT format is
better for printing (possibly after modification in OpenOffice/LibreOffice).

The type of the produced document is determined by default from the file
extension -- if extension is ``.htm`` or ``.html`` then HTML format is
produced, if extension is ``.odt`` then ODT format is saved. If file has other
extension then one has to use ``-t`` or ``--type`` option to specify document
format::

    $ ged2doc -t html archive.zip output.txt
    $ ged2doc --type=odt archive.zip output.opendoc

GEDCOM file encoding
^^^^^^^^^^^^^^^^^^^^

Properly constructed GEDCOM file should have enough information in it for
|ged2doc| to determine its encoding. In some cases it may be necessary to
specify file encoding explicitly or to change how decoding errors are handled.
By default |ged2doc| tries to determine file encoding from file contents and
it terminates for any encoding-related errors. You can use ``--encoding``
option to force it to use different encoding and ``--encoding-errors`` option
to control error handling. The argument to ``--encoding`` option is the name
of the encoding such as ``utf-8``, ``iso-8859-1``, etc. The argument to
``--encoding-errors`` option is one of the keywords:

``strict``
    Default behavior, application aborts in case of errors

``ignore``
    Application removes problematic encoded characters

``replace``
    Application replaces problematic encoded characters with special
    replacement character (�)

Here is an example of a command which forces utf-8 encoding but replaces
incorrectly encoded data::

    $ ged2doc --encoding=utf-8 --encoding-errors=replace file.ged out.html

Common output options
^^^^^^^^^^^^^^^^^^^^^

Languages
"""""""""

|ged2doc| can produce output document in different languages (currently
supporting English, Russian, Polish, and Czech). By default the language is
determined from system configuration which may not always work reliably. To
specify output language explicitly use ``-l CODE`` option, ``CODE`` is the
language code (``en`` for English, ``ru`` for Russian, ``pl`` for Polish,
``cz`` for Czech).

Date Format
"""""""""""

GEDCOM data can include dates in that can be either precise or approximate.
|ged2doc| tries to represent all possible dates in output document in a
reasonable way according to locale. Default date format in the output
document is determined by the document language but it can also be changed
via ``-d FMT`` (or ``--date-format=FMT``) option, ``FMT`` can be one of:

``YMD``
    Space-separated year, month name, and day, e.g.: ``2000 Dec 31``;
    ``2017 Dec``; ``2017``

``MDY``
    Space-separated month name, day, and year, e.g.: ``Dec 31 2000``;
    ``Dec 2017``; ``2017``

``DMY``
    Space-separated day, month name, and year, e.g.: ``31 Dec 2000``;
    ``Dec 2017``; ``2017``

``Y-M-D``
    Dash-separated year, month name, and day, e.g.: ``2000-Dec-31``;
    ``2017-Dec``; ``2017``

``D-M-Y``
    Dash-separated day, month name, and year, e.g.: ``31-Dec-2000``;
    ``Dec-2017``; ``2017``

``Y/M/D``
    Slash-separated year, month number, and day, e.g.: ``2000/12/31``;
    ``2017/12``; ``2017``

``M/D/Y``
    Slash-separated month number, day, and year, e.g.: ``12/31/2000``;
    ``12/2017``; ``2017``.

``Y.M.D``
    Dot-separated year, month number, and day, e.g.: ``2000.12.31``;
    ``2017.12``; ``2017``

``D.M.Y``
    Dot-separated day, month number, and year, e.g.: ``31.12.2000``;
    ``12.2017``; ``2017``. This is default for ``ru`` language.

``MD,Y``
    Comma after day, month number, year, e.g.: ``Dec 31, 2000``;
    ``Dec 2017``; ``2017``. This is default for ``en`` language.

Person ordering
"""""""""""""""

Ordering of persons in output document is controlled by ``--sort-order=ORDER``
option, ``ORDER`` is one of:

``last+first``
    Persons are ordered according to family (married) name and given name,
    this is default ordering.

``first+last``
    Persons are ordered according to given name and family (married) name.

``maiden+first``
    Persons are ordered according to family (maiden) name and given name.

``first+maiden``
    Persons are ordered according to given name and family (maiden) name.

By default ordering of the names is performed according to collation rules of
the current system locale. If system locale does not correspond to the
language of the document one can specify different locale using
``--locale=LOCALE`` option. ``LOCALE`` is the name of the locale and it is
usually system dependent, e.g. the name can be ``Russian`` or ``Czech`` on
Windows host or ``ru_RU.UTF-8`` or ``cs_CZ.UTF-8`` on Linux host. On Linux
it is also possible to change locale by using ``LC_ALL`` or ``LC_COLLATE``
environment variables. Check system documentation for how to install and
enable locales.

Events without dates
""""""""""""""""""""

By default |ged2doc| outputs all events including those events that do not
have associated dates (events are prefixed with "Date unknown"). To disable
printing of those events use ``--no-missing-date`` option.

Images
""""""

By default |ged2doc| adds an image for each person (if it can find it on disk),
one can disable this by using ``--no-image`` option which disables all images
in output file.

TOC
"""

Table of Contents is added by default to each document, ``--no-toc`` option
can be used to disable generation of TOC.

Statistics
""""""""""

Some statistical info is normally added to each document (e.g. name frequency),
``--no-stat`` option can be used to disable it.

Tree Width
""""""""""

For each person |ged2doc| adds a small inline graphical representation of
ancestor tree, by default four generations are represented in the tree.
Option ``-w NUMBER`` (``--tree-width NUMBER``) can be used to change the
number of generations in this tree.

Name formatting options
^^^^^^^^^^^^^^^^^^^^^^^

Different locales use different name formatting rules which may be quite
complicated. By default |ged2doc| represents person names as given name
followed by family (married) name (e.g. ``Jane Smith``) but there are also
multiple options that can change this representation:

--name-surname-first  Format names with surname in leading position,
                      e.g. ``Smith Jane``
--name-comma          Format names with surname followed by comma (only if
                      surname is in leading position), e.g. ``Smith, Jane``
--name-maiden         Format names with surname followed by maiden name in
                      parentheses, e.g. ``Jane Smith (Ivanova)``
--name-maiden-only    Format names with maiden name for surname, e.g.
                      ``Jane Ivanova``
--name-capital        Format names with surname and maiden name in all
                      capital, e.g. ``Jane SMITH``

Combining these options should produce expected effect, e.g.
``--name-surname-first --name-comma --name-capital`` would produce
something like ``SMITH (IVANOVA), Jane``.

Specifying size in options
^^^^^^^^^^^^^^^^^^^^^^^^^^

Few options below take size as a value, size can be specified in different
units. Units can be screen-based (pixels) or print-based (inches/points/mm).
You can specify sizes in any form, output document format determines actual
type of units to use. When |ged2doc| needs to convert units of one type into
another it uses a fixed conversion factor of 96 DPI (dots/pixels per inch).

Supported units are:

``px``
    Size is given in pixels, typically used for on-screen dimensions, probably
    most useful for HTML output. Example: ``100px``.

``pt``
    Size is given in points, typically used for print dimensions, one point
    is 1/72 of inch. Example: ``100pt``.

``in``
    Size is given in inches, typically used for print dimensions. Example:
    ``6.5in``.

``mm``
    Size is given in millimeters, typically used for print dimensions.
    1 in = 25.4 mm. Example: ``100mm``.

``cm``
    Size is given in centimeters, typically used for print dimensions.
    1 in = 2.54 cm. Example: ``10cm``.

Options that accept size as value have default unit type, if option default
unit is pixels then giving it value of ``300`` is the same as giving
``300px``.

HTML Options
^^^^^^^^^^^^

There are few options that are specific to HTML output:

--html-page-width SIZE    HTML page width, default unit is pixels; default value: ``800px``
--html-image-width SIZE   Image width, default unit is pixels; default value: ``300px``
--html-image-height SIZE  Image height, default unit is pixels; default value: ``300px``
-u, --html-image-upscale  Re-scale images which are smaller than size given by
    the options above. Without this option small images will be displayed
    in their actual size without re-scaling.

ODT Options
^^^^^^^^^^^

Options specific to ODT output:

--odt-page-width SIZE    Page width, default unit is inches; default value: ``6in``
--odt-page-height SIZE   Page height, default unit is inches; default value: ``9in``
--odt-margin-left SIZE   Page left margin, default unit is inches; default value: ``0.5in``
--odt-margin-right SIZE  Page right margin, default unit is inches; default value: ``0.5in``
--odt-margin-top SIZE    Page top margin, default unit is inches; default value: ``0.5in``
--odt-margin-bottom SIZE  Page bottom margin, default unit is inches; default value: ``0.25in``
--odt-image-width SIZE   Image width, default unit is inches; default value: ``2in``
--odt-image-height SIZE  Image height, default unit is inches; default value: ``2in``
--first-page NUMBER      Number of the first page; default: ``1``. Can be
        changed to something different if you plan to add extra pages
        at the beginning when printing the final document.
--odt-tree-type FORMAT   Type of image format for ancestor tree, one of emf,
        svg; default: emf

Logging
^^^^^^^

In case application crashes or produces incorrect or unexpected output it
would be helpful to produce log file with debug information and forward it
to author (see *Contributing* for how to report bugs). To produce log file
use ``--log`` option, e.g.::

    $ ged2doc --log=log.txt input.ged page.html

which will create ``log.txt`` file in a current working directory.

Examples
^^^^^^^^

To produce HTML page from GEDCOM file with default settings::

    $ ged2doc input.ged page.html

To also include images that are referenced from GEDCOM file (assuming
UNIX-style file names)::

    $ ged2doc -i /home/joe/gedcom_images input.ged page.html

Same but produce OpenDocument Text format::

    $ ged2doc -i /home/joe/gedcom_images input.ged output.odt

If GEDCOM is named ``gedcom.dump`` is in ZIP archive together with all images::

    $ ged2doc -p gedcom.dump input.zip page.html

If you need to specify different output language::

    $ ged2doc -l ru input.zip page.html

To change date representation::

    $ ged2doc -d Y-M-D input.zip page.html

To change how person name is printed::

    $ ged2doc --name-surname-first --name-comma --name-maiden input.zip page.html

To change page size of ODT document::

    $ ged2doc --odt-page-width=8.5in --odt-page-height=11in input.zip page.odt


Using Python modules
--------------------

|ged2doc| package can be used from other Python code to perform the same
conversion of GEDCOM file as command line tool does. There are three basic
objects that are needed to run conversion from Python:

- file locator instance
- language translator instance
- writer/converter instance

File locator
^^^^^^^^^^^^

File locator is an object responsible for finding/opening input files, both
GEDCOM and images. It abstracts operations with filesystem and ZIP archives
so that remaining code does not need to know details of file storage.

Factory method :py:meth:`~ged2doc.input.make_file_locator` is used to
instantiate file locator and it takes few parameters::

    from ged2doc.input import make_file_locator

    input_file = "archive.zip"    # or you can pass GEDCOM file here
    file_name_pattern = "*.ged*"
    image_path = r"C:\Users\joe\Documents\gedcom_images"
    flocator = make_file_locator(input_file, file_name_pattern, image_path)

Language translator
^^^^^^^^^^^^^^^^^^^

This object is responsible for translating output document into desired
language. :py:class:`ged2doc.i18n.I18N` implements this translation and
it needs to be installed with couple of parameters::

    from ged2doc.i18n import I18N

    lang = "ru"         # language code, "en" or "ru"
    date_fmt = "D.M.Y"  # one of the formats described above
    tr = I18N(lang, date_fmt)

Conversion
^^^^^^^^^^

Converter instance is made by instantiating specific converter class,
currently there are two such classes:

- :py:class:`ged2doc.html_writer.HtmlWriter` for conversion into HTML
- :py:class:`ged2doc.odt_writer.OdtWriter` for conversion into ODT

Constructors of these classes take several parameters:

- file locator instance
- language translator
- output file name
- dictionary with options, includes all formatting options, see
  class documentation for details

After making converter instance the code should call its
:py:meth:`~ged2doc.writer.Writer.save` method to produce output file::

    from .html_writer import HtmlWriter

    output = "document.html"
    # `flocator` and `tr` are instantiated in above examples, "..." signifies
    # multiple optional keyword arguments that control appearance
    writer = HtmlWriter(flocator, output, tr, ...)

    # save the file
    writer.save()

For more complete example check
`ged2doc.cli module <https://github.com/andy-z/ged2doc/blob/master/ged2doc/cli.py>`_.

Format-specific details
-----------------------

HTML details
^^^^^^^^^^^^

|ged2doc| produces single-page HTML document which embeds all graphics (photos
and tree graphs which are SVG structures). The size of the resulting document
can be quite large. The images are re-sampled to a specified image size before
embedding. Images that are smaller than specified image size are rescaled only
if ``--html-image-upscale`` option is given.

ODT details
^^^^^^^^^^^

|ged2doc| does not have logic to correctly paginate output document and assign
page numbers to Table of Contents entries. Instead it depends on external
tools like LibreOffice to finalize and publish the document. When document is
loaded into LibreOffice its Table of Contents needs to be refreshed -- go to
``Tools`` menu, then ``Update``, and ``Indexes and Tables`` which should
rebuild all references in ODT file.

ODT files can be opened with MS Office (Word) application, but compatibility
of MS Office with ODT format is not great and there are some known issues with
MS Word when editing documents produced by |ged2doc|:

- Images in SVG format are not fully supported by MS Office, to visualize
  ancestor trees in MS Office they need to be produced in EMF format.
  |ged2doc| supports EMF since version 0.3, where EMF is the default format
  for ancestor trees (can be changed with ``--odt-tree-type=svg`` option).
  |ged2doc| before version 0.3 cannot be used to produce EMF.
- If file with ancestor trees in EMF format was opened an saved by LibreOffice
  then MS Office cannot render those tree images. There is no reliable
  interoperability between MS Office and LibreOffice, documents should only be
  edited by the same application.
- Table of Contents is not shown when ODT file is open by MS Office, it
  has to be added manually if one needs a table of contents in the document.
