"""Module which produces HTML output.
"""

__all__ = ["HtmlWriter"]

import base64
import io
import logging
import pkg_resources
import string
from PIL import Image
from html import escape as html_escape

from ged4py import model
from .ancestor_tree import AncestorTree
from .ancestor_tree_svg import SVGTreeVisitor
from .size import Size
from . import utils
from . import writer


_log = logging.getLogger(__name__)


def TR(x):
    """This is no-op function, only used to mark translatable strings,
    to extract all strings run ``pygettext -k TR ...``
    """
    return x  # NOQA


class HtmlWriter(writer.Writer):
    """Transforms GEDCOM file into nicely formatted HTML page.

    This is a sub-class of `~ged2doc.writer.Writer` class providing
    implementation for rendering methods which transform GEDCOM info into
    HTML constructs. Constructor takes a large number of arguments which
    configure appearance of the resulting HTML page. After instantiating
    an object of this type one has to call `~ged2doc.writer.Writer.save()`
    method to produce output file.

    Parameters
    ----------
    flocator : `ged2doc.input.FileLocator`
        File locator instance.
    output : `str` or `io.TextIOBase`
        Name for the output file or file object.
    tr : `ged2doc.i18n.I18N`
        Object supporting translation.
    encoding : `str`, optional
        GEDCOM file encoding, if ``None`` then encoding is determined from
        file itself.
    encoding_errors : `str`, optional
        Controls error handling behavior during string decoding, one of
        "strict" (default), "ignore", or "replace".
    sort_order : `ged4py.model.NameOrder`, optional
        Determines ordering of person in output file, one of the constants
        defined in `ged4py.model.NameOrder` enum.
    name_fmt : `int`, optional
        Bit mask with flags from `ged2doc.name` module.
    make_images : `bool`, optional
        If ``True`` (default) then generate images for persons.
    make_stat : `bool`, optional
        If ``True`` (default) then generate statistics section.
    make_toc : `bool`, optional
        If ``True`` (default) then generate Table of Contents.
    events_without_dates : `bool`, optional
        If ``True`` (default) then show events that have no associated dates.
    page_width : `ged2doc.size.Size`
        Width of the produced HTML page.
    image_width : `ged2doc.size.Size`
        Size of the images.
    image_height : `ged2doc.size.Size`
        Size of the images.
    image_upscale : `bool`
        If True then smaller images will be re-scaled to extend to image size.
    tree_width : `int`
        Number of generations in ancestor tree.
    """
    def __init__(self, flocator, output, tr, encoding=None,
                 encoding_errors="strict",
                 sort_order=model.NameOrder.SURNAME_GIVEN, name_fmt=0,
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
        # docstring inherited from base class
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
        """Takes text with embedded references and returns properly
        escaped text with HTML links.

        Parameters
        ----------
        text : `str`
            Arbitrary text with references.

        Returns
        -------
        html : `str`
            HTML as text.
        """
        result = ""
        for piece in utils.split_refs(text):
            if isinstance(piece, tuple):
                xref, name = piece
                result += '<a href="#{0}">{1}</a>'.format(html_escape(xref),
                                                          html_escape(name))
            else:
                result += html_escape(piece)
        return result

    def _render_section(self, level, ref_id, title, newpage=False):
        # docstring inherited from base class
        self._toc += [(level, ref_id, title)]
        doc = ['<h{0} id="{1}">{2}</h{0}>\n'.format(level, ref_id,
                                                    html_escape(title))]
        for line in doc:
            self._output.write(line.encode('utf-8'))

    def _render_person(self, person, image_data, attributes, families,
                       events, notes):
        # docstring inherited from base class
        doc = []

        # image if present
        if image_data:
            img = self._get_image_fragment(image_data)
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
        # docstring inherited from base class
        doc = []
        doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Person count')), n_total)]
        doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Female count')), n_females)]
        doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Male count')), n_males)]
        for line in doc:
            self._output.write(line.encode('utf-8'))

    def _render_name_freq(self, freq_table):
        # docstring inherited from base class
        def _gencouples(namefreq):
            halflen = (len(namefreq) + 1) // 2
            for i in range(halflen):
                n1, c1 = namefreq[2 * i]
                n2, c2 = None, None
                if 2 * i + 1 < len(namefreq):
                    n2, c2 = namefreq[2 * i + 1]
                yield n1, c1, n2, c2

        total = float(sum(count for _, count in freq_table))

        tbl = ['<table class="statTable">\n']

        for name1, count1, name2, count2 in _gencouples(freq_table):

            tbl += ['<tr>\n']

            tbl += ['<td width="25%">{0}</td>'.format(name1 or '-')]
            tbl += ['<td width="20%">{0} ({1:.1%})</td>'.format(
                count1, count1 / total)]

            if count2 is not None:

                tbl += ['<td width="25%">{0}</td>'.format(name2 or '-')]
                tbl += ['<td width="20%">{0} ({1:.1%})</td>'.format(
                    count2, count2 / total)]

            tbl += ['</tr>\n']

        tbl += ['</table>\n']
        for line in tbl:
            self._output.write(line.encode('utf-8'))

    def _render_toc(self):
        # docstring inherited from base class
        section = self._tr.tr(TR("Table Of Contents"))
        doc = ['<h1>{0}</h1>\n'.format(html_escape(section))]
        lvl = 0
        for toclvl, tocid, text in self._toc:
            while lvl < toclvl:
                doc += ['<ul>']
                lvl += 1
            while lvl > toclvl:
                doc += ['</ul>']
                lvl -= 1
            doc += ['<li><a href="#{0}">{1}</a></li>\n'.format(tocid, text)]
        while lvl > 0:
            doc += ['</ul>']
            lvl -= 1
        for line in doc:
            self._output.write(line.encode('utf-8'))

    def _finalize(self):
        # docstring inherited from base class
        if self._close:
            self._output.close()

    def _get_image_fragment(self, image_data):
        """Returns <img> HTML fragment for given image data (byte array).

        Parameters
        ----------
        image_data : `bytes`
            Image data.

        Returns
        -------
        html : `str`
            HTML text containing image.
        """
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
        """Make SVG picture for parent tree.

        Parameters
        ----------
        person : `ged4py.model.Individual`
            INDI record

        Returns
        -------
        html : `list` [ `str` ]
            SVG data (HTML contents), list of strings.
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
