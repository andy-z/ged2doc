"""Module which produces ODT output.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["OdtWriter"]

from collections import namedtuple
import hashlib
import io
import logging
from PIL import Image

from ged4py import model
from .ancestor_tree import AncestorTree
from .ancestor_tree_emf import EMFTreeVisitor
from .ancestor_tree_svg import SVGTreeVisitor
from .size import Size
from . import utils
from . import writer
from odf.opendocument import OpenDocumentText
from odf import text, style, draw, table


_log = logging.getLogger(__name__)


# page layout, size and margins
PageLayout = namedtuple("PageLayout", "width height left right top bottom")

# this is no-op function, only used to mark translatable strings,
# to extract all strings run "pygettext -k TR ..."


def TR(x): return x  # NOQA


class OdtWriter(writer.Writer):
    """Transforms GEDCOM file into nicely formatted OpenDocument Text (ODT).

    This is a sub-class of :py:class:`~ged2doc.writer.Writer` class providing
    implementation for rendering methods which transform GEDCOM info into
    ODT structures. Constructor takes a large number of arguments which
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
    :param Size page_width: Page width of the produced document.
    :param Size page_height: Page height of the produced document.
    :param Size margin_left: Left page margin of the produced document.
    :param Size margin_right: Right page margin of the produced document.
    :param Size margin_top: Top page margin of the produced document.
    :param Size margin_bottom: Bottom page margin of the produced document.
    :param Size image_width: Size of the images.
    :param Size image_height: Size of the images.
    :param int tree_width: Number of generations in ancestor tree.
    :param int first_page: Number of the first generated page.
    :param str tree_format: Image format for ancestor tree, "emf" or "svg".
    """

    def __init__(self, flocator, output, tr, encoding=None,
                 encoding_errors="strict",
                 sort_order=model.ORDER_SURNAME_GIVEN, name_fmt=0,
                 make_images=True, make_stat=True, make_toc=True,
                 events_without_dates=True,
                 page_width="6in", page_height="9in",
                 margin_left="0.5in", margin_right="0.5in",
                 margin_top="0.5in", margin_bottom="0.25in",
                 image_width="2in", image_height="2in",
                 tree_width=4, first_page=1, tree_format="emf"):

        writer.Writer.__init__(self, flocator, tr, encoding=encoding,
                               encoding_errors=encoding_errors,
                               sort_order=sort_order, name_fmt=name_fmt,
                               make_images=make_images, make_stat=make_stat,
                               make_toc=make_toc,
                               events_without_dates=events_without_dates)

        self._output = output
        self._image_width = Size(image_width)
        self._image_height = Size(image_height)
        self._tree_width = tree_width
        self._first_page = first_page
        self._tree_format = tree_format

        doc = OpenDocumentText()

        # page layout
        self.layout = PageLayout(
            width=Size(page_width),
            height=Size(page_height),
            left=Size(margin_left),
            right=Size(margin_right),
            top=Size(margin_top),
            bottom=Size(margin_bottom))
        # starting page number
        self._make_layout(doc, self.layout, self._first_page)

        self.styles = self._make_styles(doc, self.layout)

        self.doc = doc

    def _make_layout(self, doc, layout, firstpage):
        # set paper dimensions
        pageLayout = style.PageLayout(name=u"pl1")
        doc.automaticstyles.addElement(pageLayout)
        plProp = style.PageLayoutProperties(pageheight=str(layout.height),
                                            pagewidth=str(layout.width),
                                            marginleft=str(layout.left),
                                            marginright=str(layout.right),
                                            margintop=str(layout.top),
                                            marginbottom=str(layout.bottom))
        pageLayout.addElement(plProp)

        # add page numbers to the footers
        footer = style.Footer()
        foostyle = style.Style(name="Footer", family="paragraph")
        foostyle.addElement(style.ParagraphProperties(textalign='center'))
        foostyle.addElement(style.TextProperties(fontsize='10pt'))
        doc.automaticstyles.addElement(foostyle)
        p = text.P(stylename=foostyle)
        p.addElement(text.PageNumber(selectpage="current",
                                     pageadjust=str(firstpage - 1)))
        footer.addElement(p)

        masterpage = style.MasterPage(name=u"Standard",
                                      pagelayoutname=pageLayout)
        masterpage.addElement(footer)
        doc.masterstyles.addElement(masterpage)

    def _make_styles(self, doc, layout):

        styles = {}

        # heading styles, occupies whole page, centered
        h1font = '22pt'
        h1topmrg = (layout.height - layout.top - layout.bottom) * 0.5
        h1topmrg -= Size(h1font)
        h1style = style.Style(name="Heading 1", family="paragraph")
        h1style.addElement(style.ParagraphProperties(
            textalign='center', breakbefore='page', margintop=str(h1topmrg)))
        h1style.addElement(style.TextProperties(fontsize=h1font,
                                                fontweight='bold'))
        doc.styles.addElement(h1style)
        styles['h1'] = h1style

        brstyle = style.Style(name="Break", family="paragraph")
        brstyle.addElement(style.ParagraphProperties(
            textalign='center', breakafter='page'))
        doc.automaticstyles.addElement(brstyle)
        styles['br'] = brstyle

        h2namestyle = style.Style(name="Heading 2 (Name)", family="paragraph")
        h2namestyle.addElement(style.ParagraphProperties(
            textalign='center', breakbefore='page', marginbottom="14pt"))
        h2namestyle.addElement(style.TextProperties(
            fontsize='14pt', fontweight='bold'))
        doc.styles.addElement(h2namestyle)
        styles['h2br'] = h2namestyle

        h2style = style.Style(name="Heading 2", family="paragraph")
        h2style.addElement(style.ParagraphProperties(
            textalign='center', margintop="12pt"))
        h2style.addElement(style.TextProperties(
            fontsize='14pt', fontweight='bold'))
        doc.styles.addElement(h2style)
        styles['h2'] = h2style

        h3style = style.Style(name="Heading 3", family="paragraph")
        # h3style.addElement(style.ParagraphProperties(textalign='center',
        # margintop="12pt", borderbottom="0.06pt solid #000000"))
        h3style.addElement(style.ParagraphProperties(
            textalign='center', margintop="12pt"))
        h3style.addElement(style.TextProperties(fontweight='bold'))
        doc.styles.addElement(h3style)
        styles['h3'] = h3style

        # style for image
        imgstyle = style.Style(
            name="ImgStyle", family="graphic", parentstylename="Graphics")
        imgstyle.addElement(style.GraphicProperties(
            verticalpos='top', verticalrel='paragraph-content',
            horizontalpos='right', horizontalrel='page-content',
            marginleft="0.1in", marginbottom="0.1in"))
        doc.automaticstyles.addElement(imgstyle)
        styles['img'] = imgstyle

        # centered paragraph
        centered = style.Style(name="centered", family="paragraph")
        centered.addElement(style.ParagraphProperties(textalign='center'))
        doc.styles.addElement(centered)
        styles['center'] = centered

        # centered frame
        frame_center = style.Style(
            name="frame-center",
            family="graphic",
            parentstylename="Graphics"
        )
        frame_center.addElement(style.GraphicProperties(
            horizontalpos="center", horizontalrel="paragraph"
        ))
        doc.automaticstyles.addElement(frame_center)
        styles['frame_center'] = frame_center

        # style for tree table
        treetablestyle = style.Style(name="TreeTableStyle", family="table")
        treetablestyle.addElement(style.TableProperties(align='center'))
        doc.automaticstyles.addElement(treetablestyle)
        styles['treetable'] = treetablestyle

        treecellstyle = style.Style(
            name="TreeTableCellStyle", family="table-cell")
        treecellstyle.addElement(style.TableCellProperties(
            verticalalign='middle', padding='0.03in'))
        doc.automaticstyles.addElement(treecellstyle)
        styles['treecell'] = treecellstyle

        treeparastyle = style.Style(
            name="TreeTableParaStyle", family="paragraph")
        treeparastyle.addElement(style.ParagraphProperties(
            textalign='center', verticalalign='middle',
            border="0.06pt solid #000000", padding='0.01in'))
        treeparastyle.addElement(style.TextProperties(fontsize='10pt'))
        doc.automaticstyles.addElement(treeparastyle)
        styles['treepara'] = treeparastyle

        return styles

    def _interpolate(self, text):
        """Takes text with embedded references and returns proporly
        escaped text with HTML links.
        """
        result = ""
        for piece in utils.split_refs(text):
            if isinstance(piece, tuple):
                xref, name = piece
                result += name
            else:
                result += piece
        return result

    def _render_prolog(self):
        """Generate initial document header/title.
        """
        pass

    def _render_section(self, level, ref_id, title, newpage=False):
        """Produces new section in the output document.

        This method should also save section reference so that TOC can be
        later produced when :py:meth:`_render_toc` method is called.

        :param int level: Section level (1, 2, 3, etc.).
        :param str ref_id: Unique section identifier.
        :param str title: Printable section name.
        """
        style = "h" + str(level)
        if newpage:
            style += "br"
        self.doc.text.addElement(text.H(text=title, outlinelevel=level,
                                        stylename=self.styles.get(style)))
        if level == 1:
            # page break after H1
            self.doc.text.addElement(text.P(text='', stylename="Break"))

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
        :param tuple tree_svg: `None` or tuple containing SVG element with
                ancestor tree (only <svg> but no XML header), MIME type of
                data, and image width and height
        """

        # image if present
        if image_data:
            imgframe = self._getImageFragment(image_data)
            if imgframe:
                p = text.P()
                imgframe.setAttribute('stylename', self.styles['img'])
                imgframe.setAttribute('anchortype', 'paragraph')
                p.addElement(imgframe)
                self.doc.text.addElement(p)

        # all attributes follow
        for attr, value in attributes:
            self.doc.text.addElement(text.P(text=attr + ": " +
                                            self._interpolate(value)))

        if families:
            hdr = self._tr.tr(TR("Spouses and children"), person.sex)
            self._render_section(3, "", hdr)
            for family in families:
                family = self._interpolate(family)
                self.doc.text.addElement(text.P(text=family))

        if events:
            hdr = self._tr.tr(TR("Events and dates"))
            self._render_section(3, "", hdr)
            for date, facts in events:
                facts = self._interpolate(facts)
                self.doc.text.addElement(text.P(text=date + ": " + facts))

        if notes:
            hdr = self._tr.tr(TR("Comments"))
            self._render_section(3, "", hdr)
            for note in notes:
                self.doc.text.addElement(text.P(text=note))

        self._make_ancestor_tree(person)

    def _render_name_stat(self, n_total, n_females, n_males):
        """Produces summary table.

        Sum of male and female counters can be lower than total count due to
        individuals with unknown/unspecified gender.

        :param int n_total: Total number of individuals.
        :param int n_females: Number of female individuals.
        :param int n_males: Number of male individuals.
        """
        items = ((TR('Person count'), n_total),
                 (TR('Female count'), n_females),
                 (TR('Male count'), n_males))
        for key, val in items:
            p = text.P(text='%s: %d' % (self._tr.tr(key), val))
            self.doc.text.addElement(p)

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

        tbl = table.Table()
        tbl.addElement(table.TableColumn())
        tbl.addElement(table.TableColumn())
        tbl.addElement(table.TableColumn())
        tbl.addElement(table.TableColumn())

        for name1, count1, name2, count2 in _gencouples(freq_table):

            row = table.TableRow()

            cell = table.TableCell()
            cell.addElement(text.P(text=name1 or '-'))
            row.addElement(cell)

            cell = table.TableCell()
            cell.addElement(text.P(text='%d (%.1f%%)' %
                                   (count1, count1 / total * 100)))
            row.addElement(cell)

            if count2 is not None:

                cell = table.TableCell()
                cell.addElement(text.P(text=name2 or '-'))
                row.addElement(cell)

                cell = table.TableCell()
                cell.addElement(text.P(text='%d (%.1f%%)' %
                                       (count2, count2 / total * 100)))
                row.addElement(cell)

            tbl.addElement(row)

        self.doc.text.addElement(tbl)

    def _render_toc(self):
        """Produce table of contents using info collected in _render_section().
        """
        self.doc.text.addElement(text.P(text='', stylename=self.styles['br']))
        toc = text.TableOfContent(name='TOC')
        tocsrc = text.TableOfContentSource(outlinelevel=2)
        title = self._tr.tr(TR("Table Of Contents"))
        toctitle = text.IndexTitleTemplate(text=title)
        tocsrc.addElement(toctitle)
        toc.addElement(tocsrc)
        self.doc.text.addElement(toc)

    def _finalize(self):
        """Finalize output.
        """
        # save the result
        if hasattr(self._output, 'write'):
            self.doc.write(self._output)
        else:
            self.doc.save(self._output)

    def _getImageFragment(self, image_data):
        '''Adds Image to the document as person's picture.
        '''

        try:
            img = Image.open(io.BytesIO(image_data))
        except Exception as exc:
            # PIL could fail for any reason, no chance to know,
            # just log an error and ignore this image
            _log.error("error while loading image: %s", exc)
            return None

        filename = u"Pictures/" + \
            hashlib.sha1(image_data).hexdigest() + '.' + img.format.lower()

        # calculate size of the frame
        maxsize = (self._image_width.inches,
                   self._image_height.inches)
        w, h = utils.resize(img.size, maxsize)
        frame = draw.Frame(width="%.3fin" % w, height="%.3fin" % h)
        imgref = self.doc.addPicture(filename, utils.img_mime_type(img),
                                     image_data)
        frame.addElement(draw.Image(href=imgref))
        return frame

    def _make_ancestor_tree(self, person):
        """"Add a picture for ancestor tree.

        :param person: Individual record
        """
        width = self.layout.width - self.layout.left - self.layout.right
        tree = AncestorTree(person, max_gen=self._tree_width, width=width, gen_dist="12pt", font_size="9pt")

        if self._tree_format == "emf":
            visitor = EMFTreeVisitor(width=tree.width, height=tree.height)
            tree.visit(visitor)
            img = visitor.makeEMF()
            if not img:
                return
            img_data, mime, width, height = img
        else:
            visitor = SVGTreeVisitor(units='in', fullxml=True)
            tree.visit(visitor)
            img = visitor.makeSVG(width=tree.width, height=tree.height)
            if not img:
                return
            img_data, mime, width, height = img
            # convert it to binary
            img_data = img_data.encode("utf_8")

        # store image
        filename = u"Pictures/" + \
            hashlib.sha1(img_data).hexdigest() + '.' + self._tree_format
        imgref = self.doc.addPicture(filename, mime, img_data)

        frame = draw.Frame(width=str(width), height=str(height), anchortype="as-char",
                           stylename=self.styles["frame_center"])
        frame.addElement(draw.Image(href=imgref))

        hdr = self._tr.tr(TR("Ancestor tree"))
        self._render_section(3, "", hdr)
        p = text.P(stylename=self.styles['center'])
        p.addElement(frame)
        self.doc.text.addElement(p)
