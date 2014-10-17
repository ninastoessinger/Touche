# coding=utf-8

from fontTools.pens.basePen import BasePen
from fontTools.misc.arrayTools import pointInRect


class FindPossibleOverlappingSegmentsPen(BasePen):
    
    def __init__(self, glyphSet, bounds, moveSegment=(0, 0)):
        BasePen.__init__(self, glyphSet)

        self.segments = set()
        self.bounds = bounds
        self.moveSegment = moveSegment
    
    def addSegment(self, segment):
        mx, my = self.moveSegment
        segment = tuple((x+mx, y+my) for x, y in segment)
        self.segments.add(segment)
    
    def _moveTo(self, pt):
        self.previousPoint = pt
        self.firstPoint = pt
    
    def _lineTo(self, pt):
        if pointInRect(pt, self.bounds):
            self.addSegment((self.previousPoint, pt))
        self.previousPoint = pt
    
    def _curveToOne(self, pt1, pt2, pt3):
        if pointInRect(pt1, self.bounds):
            self.addSegment((self.previousPoint, pt1, pt2, pt3))
        elif pointInRect(pt2, self.bounds):
            self.addSegment((self.previousPoint, pt1, pt2, pt3))
        elif pointInRect(pt3, self.bounds):
            self.addSegment((self.previousPoint, pt1, pt2, pt3))
        self.previousPoint = pt3
        
    def closePath(self):
        if self.firstPoint != self.previousPoint:
            self.lineTo(self.firstPoint)
            