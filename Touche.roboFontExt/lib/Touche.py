# coding=utf-8

"""
 Touché! 
 RoboFont extension that detects and displays glyph pairs whose bodies overlap or touch.
 v1.2 - improved and much faster – profuse thanks to Frederik Berlaen
 Nina Stössinger, October 2014
"""

import findPossibleOverlappingSegmentsPen
reload(findPossibleOverlappingSegmentsPen)

from vanilla import CheckBox, Group, List, ProgressSpinner, SquareButton, TextBox, Window
from mojo.UI import MultiLineView, OpenSpaceCenter
from mojo.roboFont import OpenWindow
from fontTools.misc.arrayTools import offsetRect, sectRect
from lib.tools.bezierTools import intersectCubicCubic, intersectCubicLine, intersectLineLine
from robofab.interface.all.dialogs import PutFile, Message
import time

class ToucheTool():
    
    def __init__(self):
        self.w = Window((180, 340), u'Touché!', minSize=(180,340), maxSize=(1000,898))
        p = 10
        w = 160
        
        # options
        self.w.options = Group((0, 0, 180, 220))
        
        buttons = {
            "checkSelBtn": {"text": "Check selected glyphs\nfor touching pairs", "callback": self.checkSel, "y": p}, 
            "checkAllBtn": {"text": "Check entire font\n(can take several minutes!)", "callback": self.checkAll, "y": 60}}            
        for button, data in buttons.iteritems():
            setattr(self.w.options, button, 
            SquareButton((p, data["y"], w, 40), data["text"], callback=data["callback"], sizeStyle="small"))
            
        self.w.options.zeroCheck = CheckBox((p, 108, w, 20), "Ignore zero-width glyphs", value=True, sizeStyle="small")
        self.w.options.progress = ProgressSpinner((82, 174, 16, 16), sizeStyle="small")
        
        # results
        self.w.results = Group((0, 220, 180, -0))
        self.w.results.show(False)
        
        textBoxes = {"stats": 24, "result": 42} 
        for box, y in textBoxes.iteritems():
            setattr(self.w.results, box, TextBox((p, y, w, 14), "", sizeStyle="small"))
            
        moreButtons = {
            "spaceView": {"text": "View all in Space Center", "callback": self.showAllPairs, "y": 65}, 
            "exportTxt": {"text": "Export as MM pair list", "callback": self.exportPairList, "y": 90}} 
        for button, data in moreButtons.iteritems():
            setattr(self.w.results, button, 
            SquareButton((p, data["y"], w, 20), data["text"], callback=data["callback"], sizeStyle="small"))
        
        # list and preview 
        self.w.outputList = List((180,0,188,-0), 
            [{"left glyph": "", "right glyph": ""}], columnDescriptions=[{"title": "left glyph"}, {"title": "right glyph"}],
            showColumnTitles=False, allowsMultipleSelection=False, enableDelete=False, selectionCallback=self.showPair)           
        self.w.preview = MultiLineView((368, 0, -0, -0), pointSize=256)
        
        self.w.open()
    
    
    # callbacks
        
    def checkAll(self, sender=None):
        self.check(useSelection=False)
        
    def checkSel(self, sender=None):
        self.check(useSelection=True)
        
    def check(self, useSelection):
        self.w.results.show(False)
        self._resizeWindow(enlarge=False)
        self.checkFont(useSelection=useSelection, excludeZeroWidth=self.w.options.zeroCheck.get())
        
    def showPair(self, sender=None):
        try:
            index = sender.getSelection()[0]
            glyphs = [self.f[gName] for gName in self.touchingPairs[index]]
            self.w.preview.set(glyphs)
        except IndexError:
            pass
            
    def showAllPairs(self, sender=None):
        # open all resulting pairs in Space Center
        rawString = ""
        for g1, g2 in self.touchingPairs:
            rawString += "/%s/%s/space" % (g1, g2)
        s = OpenSpaceCenter(self.f)
        s.setRaw(rawString)
        
    def exportPairList(self, sender=None):
        # Save the list of found touching pairs in a text file which can be read by MetricsMachine as a pair list
        path = PutFile("Choose save location", "TouchingPairs.txt")
        if path is not None:
            reportString = "#KPL:P: TouchingPairs\n"
            for g1, g2 in self.touchingPairs:
                reportString += "%s %s\n" % (g1, g2)
            fi = open(path,'w+')
            fi.write(reportString)
            fi.close()  
            
    # checking
        
    def _hasSufficientWidth(self, g):
        # to ignore combining accents and the like
        if self.excludeZeroWidth:
            # also skips 1-unit wide glyphs which many use instead of 0
            if g.width < 2:
                return False
        return True
        
    def _trimGlyphList(self, glyphList):
        newGlyphList = []
        for g in glyphList:
            if g.box is not None and self._hasSufficientWidth(g):
                newGlyphList.append(g)
        return newGlyphList
        
    def _resizeWindow(self, enlarge=True):
        posSize = self.w.getPosSize()
        targetWidth = 700 if enlarge else 180
        self.w.setPosSize((posSize[0], posSize[1], targetWidth, posSize[3]))
    
    # ok let's do this

    def checkFont(self, useSelection=False, excludeZeroWidth=True):
        f = CurrentFont()
        if f is not None:
            # initialize things
            self.w.options.progress.start()
            time0 = time.time()
            self.excludeZeroWidth = excludeZeroWidth
            self.f = f 
    
            glyphNames = f.selection if useSelection else f.keys()
            glyphList = [f[x] for x in glyphNames]
            glyphList = self._trimGlyphList(glyphList)
            
            self.touchingPairs = Touche(f).findTouchingPairs(glyphList)
        
            # display output
            self.w.results.stats.set("%d glyphs checked" % len(glyphList))
            self.w.results.result.set("%d touching pairs found" % len(self.touchingPairs))
            self.w.results.show(True)
            
            outputList = [{"left glyph": g1, "right glyph": g2} for (g1, g2) in self.touchingPairs]
            self.w.outputList.set(outputList)
            if len(self.touchingPairs) > 0:
                self.w.outputList.setSelection([0])
            else:
                self.w.preview.set("")
            
            outputButtons = [self.w.results.spaceView, self.w.results.exportTxt]
            for b in outputButtons:
                b.enable(False) if len(self.touchingPairs) == 0 else b.enable(True)
            self.w.preview.setFont(f)
            self.w.options.progress.stop()
            self._resizeWindow(enlarge=True)
        
            time1 = time.time()
            print u'Touché: finished checking %d glyphs in %.2f seconds' % (len(glyphList), time1-time0)
            
        else:
            Message(u'Touché: Can’t find a font to check')


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
        pairs = [(g1, g2) for g1 in glyphs for g2 in glyphs]
        return [(g1.name, g2.name) for (g1, g2) in pairs if self.checkPair(g1, g2)]

    def getKerning(self, g1, g2):
        return self.flatKerning.get((g1.name, g2.name), 0)

    def checkPair(self, g1, g2):
        """New checking method contributed by Frederik

        Returns a Boolean if overlapping.
        """

        kern = self.getKerning(g1, g2)

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

        # loop over all possible overlapping segments
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

OpenWindow(ToucheTool)
