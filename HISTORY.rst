=======
History
=======

0.5.0 (2020-10-09)
------------------

* Python3 goodies, use enum classes for enums

0.4.2 (2020-10-04)
------------------

* Use numpydoc style for docstrings, add extension to Sphinx
* Drop Python2 compatibility code

0.4.1 (2020-09-28)
------------------

* Use github actions instead of Travis CI

0.4.0 (2020-09-28)
------------------

* Drop Python2 support
* Python3 supported versions are 3.6 - 3.8

0.3.1 (2020-08-30)
------------------

* No changes in ged2doc code, new version is to build Windows app with latest
  ged4py version (v0.2.4) which fixes Genery.com dialect detection.

0.3.0 (2020-08-02)
------------------

* New module `dumbemf` implements a subset of EMF drawing primitives to
  support EMF representation of ancestor trees.
* Ancestor tree in ODT output is now in EMF format by default, there is an
  option to use SVG format as in previous versions

0.2.1 (2020-07-18)
------------------

* Fix DateValue error and Python2 compatibility issues (#28).

0.2.0 (2020-07-05)
------------------

* Update for improved DATE support in ged4py

0.1.16 (2018-09-08)
-------------------

* Add protection from exceptions in Pillow

0.1.15 (2018-06-02)
-------------------

* Add Czech translation (kudos to @Mejstro)
* Add --locale option
* Fix for SVG file (ancestor trees) headers

0.1.14 (2018-05-17)
-------------------

* Improve logging and error reporting

0.1.13 (2018-04-23)
-------------------

* Fix for event date comparison (#15)

0.1.12 (2018-04-21)
-------------------

* Fixed (hopefully) crash when dealing with GIF images.
* Added Polish translation (kudos to @voyager212)
* Improved image search algorithm for on-disk and zipped locations

0.1.11 (2018-04-07)
-------------------

* Output events without dates, and add option to disable it

0.1.10 (2018-04-02)
-------------------

* Changed Russian translation for "Maiden name"

0.1.9 (2018-02-03)
------------------

* Improve format of generic events and attributes, use TYPE as event type
* Add "cause" to formatted event if "CAUS" tag is present

0.1.8 (2018-01-31)
------------------

* Require ged4py 0.1.4 or later
* This improves name parsing for ALTREE dialect

0.1.7 (2018-01-28)
------------------

* Fixed bug causing exception for small images:
  UnboundLocalError: local variable 'imgsize' referenced before assignment

0.1.6 (2018-01-21)
------------------

* Update docs, add russian translation for usage/installation

0.1.5 (2018-01-16)
------------------

* Try to open images using full path

0.1.4 (2018-01-16)
------------------

* Python3 fixes, bytes handling

0.1.3 (2018-01-14)
------------------

* add --version option to print ged2doc/ged4py versions

0.1.2 (2018-01-13)
------------------

* Small fix for packaging

0.1.1 (2018-01-07)
------------------

* Add support for ODT output.
* Add options for names formatting
* Automatic determination of output format from file extension

0.1.0 (2017-10-20)
------------------

* First release on PyPI.
* Only supporting HTML output for now.
