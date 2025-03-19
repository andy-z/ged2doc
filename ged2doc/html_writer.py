"""Module which produces HTML output."""

from __future__ import annotations

__all__ = ["HtmlWriter"]

import base64
import io
import logging
import string
from collections.abc import Iterator
from html import escape as html_escape
from importlib import resources
from typing import TYPE_CHECKING

from ged4py import model
from PIL import Image

from . import utils, writer
from .ancestor_tree import AncestorTree
from .ancestor_tree_svg import SVGTreeVisitor
from .name import NameFormat
from .size import Size

if TYPE_CHECKING:
    from .i18n import I18N
    from .input import FileLocator

_log = logging.getLogger(__name__)


def TR(x: str) -> str:
    """Mark translatable strings. This is no-op function, only used
    to extract all strings run ``pygettext -k TR ...``.
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
    name_fmt : `ged2doc.name.NameFormat`, optional
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

    def __init__(
        self,
        flocator: FileLocator,
        output: str | io.BufferedIOBase,
        tr: I18N,
        encoding: str | None = None,
        encoding_errors: str = "strict",
        sort_order: model.NameOrder = model.NameOrder.SURNAME_GIVEN,
        name_fmt: NameFormat = NameFormat(0),
        make_images: bool = True,
        make_stat: bool = True,
        make_toc: bool = True,
        events_without_dates: bool = True,
        page_width: str = "800px",
        image_width: str = "300px",
        image_height: str = "300px",
        image_upscale: bool = False,
        tree_width: int = 4,
    ):
        writer.Writer.__init__(
            self,
            flocator,
            tr,
            encoding=encoding,
            encoding_errors=encoding_errors,
            sort_order=sort_order,
            name_fmt=name_fmt,
            make_images=make_images,
            make_stat=make_stat,
            make_toc=make_toc,
            events_without_dates=events_without_dates,
        )

        self._page_width = Size(page_width)
        self._image_width = Size(image_width)
        self._image_height = Size(image_height)
        self._image_upscale = image_upscale
        self._tree_width = tree_width

        self._output: io.BufferedIOBase
        if isinstance(output, str):
            self._output = open(output, "wb")
            self._close = True
        else:
            self._output = output
            self._close = False
        self._toc: list[tuple[int, str, str]] = []

    def _render_prolog(self) -> None:
        # docstring inherited from base class
        doc = ["<!DOCTYPE html>"]
        doc += ["<html>", "<head>"]
        doc += ['<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n']
        doc += ["<title>", "Family Tree", "</title>\n"]
        d = dict(page_width=self._page_width ^ "px")
        style = resources.files("ged2doc").joinpath("data/styles/default").read_text()
        doc += [string.Template(style).substitute(d)]
        doc += ["</head>\n", "<body>\n"]
        doc += ['<div id="contents_div"/>\n']
        for line in doc:
            self._output.write(line.encode("utf-8"))

    def _interpolate(self, text: str) -> str:
        """Take text with embedded references and return properly
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
                result += f'<a href="#{html_escape(xref)}">{html_escape(name)}</a>'
            else:
                result += html_escape(piece)
        return result

    def _render_section(self, level: int, ref_id: str, title: str, newpage: bool = False) -> None:
        # docstring inherited from base class
        self._toc += [(level, ref_id, title)]
        doc = [f'<h{level} id="{ref_id}">{html_escape(title)}</h{level}>\n']
        for line in doc:
            self._output.write(line.encode("utf-8"))

    def _render_person(
        self,
        person: model.Individual,
        image_data: bytes | None,
        attributes: list[tuple],
        families: list[str],
        events: list[tuple],
        notes: list[str],
    ) -> None:
        # docstring inherited from base class
        doc = []

        # image if present
        if image_data:
            img = self._get_image_fragment(image_data)
            if img:
                doc += [img]

        # all attributes follow
        for attr, value in attributes:
            doc += ["<p>" + self._interpolate(attr) + ": " + self._interpolate(value) + "</p>\n"]

        if families:
            hdr = self._tr.tr(TR("Spouses and children"), person.sex)
            doc += ["<h3>" + html_escape(hdr) + "</h3>\n"]
            for family in families:
                family = self._interpolate(family)
                doc += ["<p>" + family + "</p>\n"]

        if events:
            hdr = self._tr.tr(TR("Events and dates"))
            doc += ["<h3>" + html_escape(hdr) + "</h3>\n"]
            for date, facts in events:
                facts = self._interpolate(facts)
                doc += ["<p>" + html_escape(date) + ": " + facts + "</p>\n"]

        if notes:
            hdr = self._tr.tr(TR("Comments"))
            doc += ["<h3>" + html_escape(hdr) + "</h3>\n"]
            for note in notes:
                note = self._interpolate(note)
                doc += ["<p>" + note + "</p>\n"]

        # plot ancestors tree
        doc += self._make_ancestor_tree(person)

        for line in doc:
            self._output.write(line.encode("utf-8"))

    def _render_name_stat(self, n_total: int, n_females: int, n_males: int) -> None:
        # docstring inherited from base class
        doc = []
        txt = self._tr.tr(TR("Person count"))
        doc += [f"<p>{txt}: {n_total}</p>"]
        txt = self._tr.tr(TR("Female count"))
        doc += [f"<p>{txt}: {n_females}</p>"]
        txt = self._tr.tr(TR("Male count"))
        doc += [f"<p>{txt}: {n_males}</p>"]
        for line in doc:
            self._output.write(line.encode("utf-8"))

    def _render_name_freq(self, freq_table: list[tuple[str, int]]) -> None:
        # docstring inherited from base class

        def _gencouples(namefreq: list[tuple[str, int]]) -> Iterator[tuple[str, int, str | None, int | None]]:
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
            tbl += ["<tr>\n"]

            tbl += [f'<td width="25%">{name1 or "-"}</td>']
            tbl += [f'<td width="20%">{count1} ({count1 / total:.1%})</td>']

            if count2 is not None:
                tbl += [f'<td width="25%">{name2 or "-"}</td>']
                tbl += [f'<td width="20%">{count2} ({count2 / total:.1%})</td>']

            tbl += ["</tr>\n"]

        tbl += ["</table>\n"]
        for line in tbl:
            self._output.write(line.encode("utf-8"))

    def _render_toc(self) -> None:
        # docstring inherited from base class
        section = self._tr.tr(TR("Table Of Contents"))
        doc = [f"<h1>{html_escape(section)}</h1>\n"]
        lvl = 0
        for toclvl, tocid, text in self._toc:
            while lvl < toclvl:
                doc += ["<ul>"]
                lvl += 1
            while lvl > toclvl:
                doc += ["</ul>"]
                lvl -= 1
            doc += [f'<li><a href="#{tocid}">{text}</a></li>\n']
        while lvl > 0:
            doc += ["</ul>"]
            lvl -= 1
        for line in doc:
            self._output.write(line.encode("utf-8"))

    def _finalize(self) -> None:
        # docstring inherited from base class
        if self._close:
            self._output.close()

    def _get_image_fragment(self, image_data: bytes) -> str | None:
        """Return <img> HTML fragment for given image data (byte array).

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
            tag = '<img class="personImage"{imgsize} src="data:{mime};base64,{data}"/>'
            data = base64.b64encode(image_data).decode("ascii")
            return tag.format(mime=utils.img_mime_type(img), data=data, imgsize=imgsize)

        else:
            # new image, need to convert it to bytes
            imgfile = io.BytesIO()
            mimetype = utils.img_save(newimg, imgfile)
            if mimetype:
                tag = '<img class="personImage" src="data:{mime};base64,{data}"/>'
                data = base64.b64encode(imgfile.getvalue()).decode("ascii")
                return tag.format(mime=mimetype, data=data)
            return None

    def _make_ancestor_tree(self, person: model.Individual) -> list[str]:
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
        width = self._page_width ^ "px"
        tree = AncestorTree(person, max_gen=self._tree_width, width=width, gen_dist="12pt", font_size="9pt")
        visitor = SVGTreeVisitor(units="px", fullxml=False)
        tree.visit(visitor)
        img = visitor.makeSVG(width=tree.width, height=tree.height)
        doc = []
        if img is not None:
            tree_svg = img[0]
            hdr = self._tr.tr(TR("Ancestor tree"))
            doc += ["<h3>" + html_escape(hdr) + "</h3>\n"]
            doc += ['<div class="centered">\n']
            doc += [tree_svg]
            doc += ["</div>\n"]
        else:
            doc += ['<svg width="100%" height="1pt"/>\n']
        return doc
