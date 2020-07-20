"""Module which produces HTML output.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["HtmlWriter"]

import base64
import io
import logging
import pkg_resources
import string
from PIL import Image
import six
if not six.PY2:
    from html import escape as html_escape
else:
    from cgi import escape as html_escape

from ged4py import model
from .ancestor_tree import AncestorTree
from .ancestor_tree_svg import SVGTreeVisitor
from .size import Size
from . import utils
from . import writer


_log = logging.getLogger(__name__)

# this is no-op function, only used to mark translatable strings,
# to extract all strings run "pygettext -k TR ..."


def TR(x): return x  # NOQA


class HtmlWriter(writer.Writer):
    """Transforms GEDCOM file into nicely formatted HTML page.

    This is a sub-class of :py:class:`~ged2doc.writer.Writer` class providing
    implementation for rendering methods which transform GEDCOM info into
    HTML constructs. Constructor takes a large number of arguments which
    configure appearance of the resulting HTML page. After instantiating
    an object of this type one has to call
    :py:meth:`~ged2doc.writer.Writer.save` method to produce output file.

    :param flocator: Instance of :py:class:`ged2doc.input.FileLocator`
    :param str output: Name for the output file or file object
    :param tr: Instance of :py:class:`ged2doc.i18n.I18N` class
    :param str encoding: GEDCOM file encoding, if ``None`` then encoding is
        determined from file itself
    :param str encoding_errors: Controls error handling behavior during string
        decoding, one of "strict" (default), "ignore", or "replace".
    :param sort_order: Determines ordering of person in output file, one of
        the constants defined in :py:mod:`ged4py.model` module.
    :param int name_fmt: Bit mask with flags from :py:mod:`ged2doc.name`
    :param bool make_images: If ``True`` (default) then generate images for
        persons.
    :param bool make_stat: If ``True`` (default) then generate statistics
        section.
    :param bool make_toc: If ``True`` (default) then generate Table of
        Contents.
    :param bool events_without_dates: If ``True`` (default) then show events
        that have no associated dates.
    :param Size page_width: Width of the produced HTML page.
    :param Size image_width: Size of the images.
    :param Size image_height: Size of the images.
    :param bool image_upscale: If True then smaller images will be
        re-scaled to extend to image size.
    :param int tree_width: Number of generations in ancestor tree.
    """

    def __init__(self, flocator, output, tr, encoding=None,
                 encoding_errors="strict",
                 sort_order=model.ORDER_SURNAME_GIVEN, name_fmt=0,
                 make_images=True, make_stat=True, make_toc=True,
                 events_without_dates=True,
                 page_width="800px", image_width="300px",
                 image_height="300px", image_upscale=False,
                 tree_width=4):

        writer.Writer.__init__(self, flocator, tr, encoding=encoding,
                               encoding_errors=encoding_errors,
                               sort_order=sort_order, name_fmt=name_fmt,
                               make_images=make_images, make_stat=make_stat,
                               make_toc=make_toc,
                               events_without_dates=events_without_dates)

        self._page_width = Size(page_width)
        self._image_width = Size(image_width)
        self._image_height = Size(image_height)
        self._image_upscale = image_upscale
        self._tree_width = tree_width

        if hasattr(output, 'write'):
            self._output = output
            self._close = False
        else:
            self._output = open(output, 'wb')
            self._close = True
        self._toc = []

    def _render_prolog(self):
        """Generate initial document header/title.
        """
        doc = ['<!DOCTYPE html>']
        doc += ['<html>', '<head>']
        doc += ['<meta http-equiv="Content-Type" content="text/html;'
                ' charset=utf-8">\n']
        doc += ['<title>', 'Family Tree', '</title>\n']
        d = dict(page_width=self._page_width ^ 'px')
        style = pkg_resources.resource_string(__name__, "data/styles/default")
        style = style.decode('utf-8')
        doc += [string.Template(style).substitute(d)]
        doc += ['</head>\n', '<body>\n']
        doc += ['<div id="contents_div"/>\n']
        for line in doc:
            self._output.write(line.encode('utf-8'))

    def _interpolate(self, text):
        """Takes text with embedded references and returns proporly
        escaped text with HTML links.
        """
        result = ""
        for piece in utils.split_refs(text):
            if isinstance(piece, tuple):
                xref, name = piece
                result += u'<a href="#{0}">{1}</a>'.format(html_escape(xref),
                                                           html_escape(name))
            else:
                result += html_escape(piece)
        return result

    def _render_section(self, level, ref_id, title, newpage=False):
        """Produces new section in the output document.

        This method should also save section reference so that TOC can be
        later produced when :py:meth:`_render_toc` method is called.

        :param int level: Section level (1, 2, 3, etc.).
        :param str ref_id: Unique section identifier.
        :param str title: Printable section name.
        """
        self._toc += [(level, ref_id, title)]
        doc = [u'<h{0} id="{1}">{2}</h{0}>\n'.format(level, ref_id,
                                                     html_escape(title))]
        for line in doc:
            self._output.write(line.encode('utf-8'))

    def _render_person(self, person, image_data, attributes, families,
                       events, notes):
        """Output person information.

        TExtual information in parameters to this method can include
        references to other persons (e.g. moter/father). Such references are
        embedded into text in encoded format determined by
        :py:meth:`_person_ref` method. It is responsibility of the subclasses
        to extract these references from text and re-encode them using proper
        bacenf representation.

        :param person: :py:class:`ged4py.Individual` instance
        :param bytes image_data: Either `None` or binary image data (typically
                content of JPEG image)
        :param list attributes: List of (attr_name, text) tuples, may be empty.
        :param list families: List of strings (possibly empty), each string
                contains description of one family and should be typically
                rendered as a separate paragraph.
        :param list events: List of (date, text) tuples, may be empty. Date
                is properly formatted string and does not need any other
                formatting.
        :param list notes: List of strings, each string should be rendered
                as separate paragraph.
        """

        doc = []

        # image if present
        if image_data:
            img = self._getImageFragment(image_data)
            if img:
                doc += [img]

        # all attributes follow
        for attr, value in attributes:
            doc += ['<p>' + self._interpolate(attr) + ": " +
                    self._interpolate(value) + '</p>\n']

        if families:
            hdr = self._tr.tr(TR("Spouses and children"), person.sex)
            doc += ['<h3>' + html_escape(hdr) + '</h3>\n']
            for family in families:
                family = self._interpolate(family)
                doc += ['<p>' + family + '</p>\n']

        if events:
            hdr = self._tr.tr(TR("Events and dates"))
            doc += ['<h3>' + html_escape(hdr) + '</h3>\n']
            for date, facts in events:
                facts = self._interpolate(facts)
                doc += ['<p>' + html_escape(date) + ": " + facts +
                        '</p>\n']

        if notes:
            hdr = self._tr.tr(TR("Comments"))
            doc += ['<h3>' + html_escape(hdr) + '</h3>\n']
            for note in notes:
                note = self._interpolate(note)
                doc += ['<p>' + note + '</p>\n']

        # plot ancestors tree
        doc += self._make_ancestor_tree(person)

        for line in doc:
            self._output.write(line.encode('utf-8'))

    def _render_name_stat(self, n_total, n_females, n_males):
        """Produces summary table.

        Sum of male and female counters can be lower than total count due to
        individuals with unknown/unspecified gender.

        :param int n_total: Total number of individuals.
        :param int n_females: Number of female individuals.
        :param int n_males: Number of male individuals.
        """
        doc = []
        doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Person count')), n_total)]
        doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Female count')), n_females)]
        doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Male count')), n_males)]
        for line in doc:
            self._output.write(line.encode('utf-8'))

    def _render_name_freq(self, freq_table):
        """Produces name statistics table.

        :param freq_table: list of (name, count) tuples.
        """
        def _gencouples(namefreq):
            halflen = (len(namefreq) + 1) // 2
            for i in range(halflen):
                n1, c1 = namefreq[2 * i]
                n2, c2 = None, None
                if 2 * i + 1 < len(namefreq):
                    n2, c2 = namefreq[2 * i + 1]
                yield n1, c1, n2, c2

        total = float(sum(count for _, count in freq_table))

        tbl = [u'<table class="statTable">\n']

        for name1, count1, name2, count2 in _gencouples(freq_table):

            tbl += [u'<tr>\n']

            tbl += [u'<td width="25%">{0}</td>'.format(name1 or '-')]
            tbl += [u'<td width="20%">{0} ({1:.1%})</td>'.format(
                count1, count1 / total)]

            if count2 is not None:

                tbl += [u'<td width="25%">{0}</td>'.format(name2 or '-')]
                tbl += [u'<td width="20%">{0} ({1:.1%})</td>'.format(
                    count2, count2 / total)]

            tbl += [u'</tr>\n']

        tbl += [u'</table>\n']
        for line in tbl:
            self._output.write(line.encode('utf-8'))

    def _render_toc(self):
        """Produce table of contents using info collected in _render_section().
        """
        section = self._tr.tr(TR("Table Of Contents"))
        doc = [u'<h1>{0}</h1>\n'.format(html_escape(section))]
        lvl = 0
        for toclvl, tocid, text in self._toc:
            while lvl < toclvl:
                doc += ['<ul>']
                lvl += 1
            while lvl > toclvl:
                doc += ['</ul>']
                lvl -= 1
            doc += [u'<li><a href="#{0}">{1}</a></li>\n'.format(tocid,
                                                                text)]
        while lvl > 0:
            doc += ['</ul>']
            lvl -= 1
        for line in doc:
            self._output.write(line.encode('utf-8'))

    def _finalize(self):
        """Finalize output.
        """
        if self._close:
            self._output.close()

    def _getImageFragment(self, image_data):
        '''Returns <img> HTML fragment for given image data (byte array).
        '''

        try:
            imgfile = io.BytesIO(image_data)
            img = Image.open(imgfile)
        except Exception as exc:
            # PIL could fail for any reason, no chance to know,
            # just log an error and ignore this image
            _log.error("error while loading image: %s", exc)
            return None

        maxsize = (self._image_width.px, self._image_height.px)
        newimg = utils.img_resize(img, maxsize)
        if newimg is img:
            # means size was not changed and image is smaller
            # than box, we may want to extend it
            imgsize = ""
            if self._image_upscale:
                extend = utils.resize(img.size, maxsize, False)
                imgsize = ' width="{}" height="{}"'.format(*extend)

            # reuse original image data
            tag = '<img class="personImage"{imgsize} '\
                  'src="data:{mime};base64,{data}"/>'
            data = base64.b64encode(image_data).decode('ascii')
            return tag.format(mime=utils.img_mime_type(img),
                              data=data, imgsize=imgsize)

        else:
            # new image, need to convert it to bytes
            imgfile = io.BytesIO()
            mimetype = utils.img_save(newimg, imgfile)
            if mimetype:
                tag = '<img class="personImage" '\
                      'src="data:{mime};base64,{data}"/>'
                data = base64.b64encode(imgfile.getvalue()).decode('ascii')
                return tag.format(mime=mimetype, data=data)

    def _make_ancestor_tree(self, person):
        """"Returns SVG picture for parent tree or None.

        :param person: Individual record
        :return: Image data (XML contents), bytes
        """
        width = self._page_width ^ 'px'
        tree = AncestorTree(person, max_gen=self._tree_width, width=width, gen_dist="12pt", font_size="9pt")
        visitor = SVGTreeVisitor(units='px', fullxml=False)
        tree.visit(visitor)
        img = visitor.makeSVG(width=tree.width, height=tree.height)
        doc = []
        if img is not None:
            tree_svg = img[0]
            hdr = self._tr.tr(TR("Ancestor tree"))
            doc += ['<h3>' + html_escape(hdr) + '</h3>\n']
            doc += ['<div class="centered">\n']
            doc += [tree_svg]
            doc += ['</div>\n']
        else:
            doc += ['<svg width="100%" height="1pt"/>\n']
        return doc
