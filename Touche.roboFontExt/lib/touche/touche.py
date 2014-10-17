# coding=utf-8

import findPossibleOverlappingSegmentsPen
reload(findPossibleOverlappingSegmentsPen)

from fontTools.misc.arrayTools import offsetRect, sectRect
from lib.tools.bezierTools import intersectCubicCubic, intersectCubicLine, intersectLineLine


class Touche(object):
    """Checks a font for touching glyphs.
    
        font = CurrentFont()
        a, b = font['a'], font['b']
        touche = Touche(font)
        touche.checkPair(a, b)
        touche.findTouchingPairs([a, b])
    
    Public methods: checkPair, findTouchingPairs
    """

    def __init__(self, font):
        self.font = font
        self.flatKerning = font.naked().flatKerning

    def findTouchingPairs(self, glyphs):
        """Finds all touching pairs in a list of glyphs.

        Returns a list of tuples containing the names of overlapping glyphs
        """
        
        # lookup all sidebearings
        lsb, rsb = ({} for i in range(2))
        for g in glyphs:
            lsb[g], rsb[g] = g.leftMargin, g.rightMargin
        self.lsb, self.rsb = lsb, rsb
        
        pairs = [(g1, g2) for g1 in glyphs for g2 in glyphs]
        return [(g1.name, g2.name) for (g1, g2) in pairs if self.checkPair(g1, g2)]

    def getKerning(self, g1, g2):
        return self.flatKerning.get((g1.name, g2.name), 0)

    def checkPair(self, g1, g2):
        """New checking method contributed by Frederik

        Returns a Boolean if overlapping.
        """

        kern = self.getKerning(g1, g2)
        
        # Check sidebearings first (PvB's idea)
        if self.rsb[g1] + self.lsb[g2] + kern > 0:
            return False

        # get the bounds and check them
        bounds1 = g1.box
        if bounds1 is None:
            return False
        bounds2 = g2.box
        if bounds2 is None:
            return False    

        # shift bounds2
        bounds2 = offsetRect(bounds2, g1.width+kern, 0)
        # check for intersection bounds
        intersectingBounds, _ = sectRect(bounds1, bounds2)
        if not intersectingBounds:
            return False
        # move bounds1 back, moving bounds is faster then moving all coordinates in a glyph
        bounds1 = offsetRect(bounds1, -g2.width-kern, 0)

        # create a pen for g1 with a shifted rect, draw the glyph into the pen
        pen1 = findPossibleOverlappingSegmentsPen.FindPossibleOverlappingSegmentsPen(g1.getParent(), bounds2)
        g1.draw(pen1)

        # create a pen for g2 with a shifted rect and move each found segment with the width and kerning
        pen2 = findPossibleOverlappingSegmentsPen.FindPossibleOverlappingSegmentsPen(g2.getParent(), bounds1, (g1.width+kern, 0))
        # draw the glyph into the pen
        g2.draw(pen2)

        for segment1 in pen1.segments:
            for segment2 in pen2.segments:
                if len(segment1) == 4 and len(segment2) == 4:
                    a1, a2, a3, a4 = segment1
                    b1, b2, b3, b4 = segment2
                    result = intersectCubicCubic(a1, a2, a3, a4, b1, b2, b3, b4)
                elif len(segment1) == 4:
                    p1, p2, p3, p4 = segment1
                    a1, a2 = segment2
                    result = intersectCubicLine(p1, p2, p3, p4, a1, a2)
                elif len(segment2) == 4:
                    p1, p2, p3, p4 = segment2
                    a1, a2 = segment1
                    result = intersectCubicLine(p1, p2, p3, p4, a1, a2)
                else:
                    a1, a2 = segment1
                    b1, b2 = segment2
                    result = intersectLineLine(a1, a2, b1, b2)
                if result.status == "Intersection":
                    return True

        return False
