# coding=utf-8

"""
 Touché! 
 RoboFont extension that detects and displays glyph pairs whose bodies overlap or touch.
 v1.0 - October 2014
 nina@typologic.nl
"""

from robofab.interface.all.dialogs import PutFile, Message
from vanilla import CheckBox, Group, List, ProgressSpinner, SquareButton, TextBox, Window
from mojo.UI import MultiLineView, OpenSpaceCenter
from mojo.roboFont import OpenWindow
import time

import shiftedDigestPointPen
import findPointOnSegment


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
            glyphs = [self.f[gName] for gName in self.touche[index]]
            self.w.preview.set(glyphs)
        except IndexError:
            pass
            
    def showAllPairs(self, sender=None):
        # open all resulting pairs in Space Center
        rawString = ""
        for g1, g2 in self.touche:
            rawString += "/%s/%s/space" % (g1, g2)
        s = OpenSpaceCenter(self.f)
        s.setRaw(rawString)
        
    def exportPairList(self, sender=None):
        # Save the list of found touching pairs in a text file which can be read by MetricsMachine as a pair list
        path = PutFile("Choose save location", "TouchingPairs.txt")
        if path is not None:
            reportString = "#KPL:P: TouchingPairs\n"
            for g1, g2 in self.touche:
                reportString += "%s %s\n" % (g1, g2)
            fi = open(path,'w+')
            fi.write(reportString)
            fi.close()  
            
    # checking
    
    def identifyTouchingPair(self, g1, g2):
        # only continue if bounding boxes overlap
        if self._boxOverlap(g1, g2):
            # so do their bodies overlap?
            if self._booleanCheck(g1, g2):
                return True
            # or do the contours merely touch in some point?
            elif self._sharesPoints(g1, g2):
                return True
        return False
        
    def _boxExists(self, g):
        if g.box is not None:
            return True
        return False
        
    def _hasSufficientWidth(self, g):
        # to ignore combining accents and the like
        if self.excludeZeroWidth:
            # also skips 1-unit wide glyphs which many use instead of 0
            if g.width < 2:
                return False
        return True
        
    def _boxOverlap(self, g1, g2):
        kern = self._findKern(g1, g2)
        dist = g1.width + kern
        self.distanceDict[(g1, g2)] = dist
        # horizontal overlap
        if g2.box[0] + dist <= g1.box[2]:
            if g2.box[2] + dist > g1.box[0]:
                # vertical overlap
                if g1.box[3] > g2.box[1] and g2.box[3] > g1.box[1]:
                    return True
        return False
        
            
    def _booleanCheck(self, g1, g2):
        # build shifted glyph
        tmpShifted = RGlyph()
        dist = self.distanceDict[(g1, g2)]
        tmpShifted.appendGlyph(g2.copy(), offset=(dist,0))
        # make boolean intersection to see if the 2 glyphs share a common area
        o = tmpShifted & g1
        if o.isEmpty():
            # now we know they don't *overlap*, but maybe they just touch along a collinear vector?
            # make union + compare contour count
            t = tmpShifted | g1
            if len(t) < len(g2) + len(g1):
                return True
            return False
        return True
        
        
    def _sharesPoints(self, g1, g2):
        # this fires if 2 on-curve points from the two glyphs respectively come to lie exactly on top of each other
        # this makes false positives
        onCurvePointList = {}
        allPointList = {}
        if (g1 != g2): # false positives for successions of the same glyph
            dist = self.distanceDict[(g1, g2)]
            #print "dist /%s/%s:" % (g1.name, g2.name), dist
            pens = {
                g1: shiftedDigestPointPen.ShiftedDigestPointPen((0,0)),
                g2: shiftedDigestPointPen.ShiftedDigestPointPen((dist,0))}
            for g in [g1, g2]:
                g.drawPoints(pens[g])
                onCurvePointList[g] = pens[g].getPointDigest()
                allPointList[g] = pens[g].getPointDigest(onCurveOnly=False)
            if len(onCurvePointList[g1]) > 0 and len(onCurvePointList[g2]) > 0:
                for p1 in onCurvePointList[g1]:
                    for p2 in onCurvePointList[g2]:
                        if p1[0] == p2[0]:
                            return True
                    
            # Check if an on-curve point touches the other contour in a place where there isn't a point
            # I'm retiring this for the moment because it makes false positives and does more harm than good
            """
            directions = [(g1, g2), (g2, g1)]
            for item1, item2 in directions:
                if len(onCurvePointList[item1]) > 0 and len(allPointList[item2]) > 0:
                    for p1 in onCurvePointList[item1]:
                        print "checking point at coord", p1[0], "in glyph", item1.name
                        #p2s = allPointList[item2]
                        p2s = onCurvePointList[item2]
                        for i in range(len(p2s)):
                            found = False
                            h = i-1 if i > 0 else len(p2s) - 1
                            if p2s[i][1] == "line":
                                startPoint = p2s[h][0] 
                                endPoint   = p2s[i][0] 
                                found = findPointOnSegment.findPointOnLine(startPoint, endPoint, p1[0])
                            # and curves? see below *
                            if found:
                                #print "found: point at", p1[0], "touches line between", startPoint, "and", endPoint
                                return True
            """
        return False
        """
        * This does not check for cases (for now) where a contour outside of a point touches a contour outside of a point, or a corner touches a curve (outside of a point) in the second contour, without producing an overlap which would have been caught earlier. It seems quite unlikely that those would exactly touch in one coordinate (I can’t even come up with a good testing scenario for this). Or should coordinates be rounded, allowing near-misses to qualify too? Not sure.
        """
        

        
    # kerning stuff
        
    def _findKern(self, g1, g2):
        # Find the relevant kerning value for a given pair
        # glyph - glyph
        key = (g1.name, g2.name)
        if self.f.kerning.has_key(key):
            return self.f.kerning[key]
        # group - glyph
        if self.kernGroups.has_key(g1.name):
            for groups in self.kernGroups[g1.name]:
                key = (groups, g2.name)
                if self.f.kerning.has_key(key):
                    return self.f.kerning[key]
        # glyph - group
        if self.kernGroups.has_key(g2.name):
            for groups in self.kernGroups[g2.name]:
                key = (g1.name, groups)
                if self.f.kerning.has_key(key):
                    return self.f.kerning[key]   
        # group - group          
        if self.kernGroups.has_key(g1.name) and self.kernGroups.has_key(g2.name):
            for groups1 in self.kernGroups[g1.name]:
                for groups2 in self.kernGroups[g2.name]:
                    key = (groups1, groups2)
                    if self.f.kerning.has_key(key):
                        return self.f.kerning[key]
        return 0
        
    def _buildKernGroupDict(self, glyphList):
        # Initially collect kern groups for easy referencing by self._findKern
        kernGroups = {}
        for g in glyphList:
            groups = self.f.groups.findGlyph(g.name)
            if len(groups) > 0:
                kernGroups[g.name] = groups
        return kernGroups
        
        
    # some other helper stuff
        
    def _trimGlyphList(self, glyphList):
        newGlyphList = []
        for g in glyphList:
            if self._boxExists(g) and self._hasSufficientWidth(g):
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
            glyphCount = len(glyphList)
            glyphList = self._trimGlyphList(glyphList)
            
            self.kernGroups = self._buildKernGroupDict(glyphList)
            self.distanceDict = {}
            self.touche = []

            # check pairs
            for g1 in glyphList:
                for g2 in glyphList:
                    if self.identifyTouchingPair(g1, g2):
                        self.touche.append((g1.name, g2.name))
        
            # display output
            self.w.results.stats.set("%d glyphs checked" % glyphCount)
            self.w.results.result.set("%d touching pairs found" % len(self.touche))
            self.w.results.show(True)
            
            outputList = [{"left glyph": g1, "right glyph": g2} for (g1, g2) in self.touche]
            self.w.outputList.set(outputList)
            if len(self.touche) > 0:
                self.w.outputList.setSelection([0])
            else:
                self.w.preview.set("")
            
            outputButtons = [self.w.results.spaceView, self.w.results.exportTxt]
            for b in outputButtons:
                b.enable(False) if len(self.touche) == 0 else b.enable(True)
            self.w.preview.setFont(f)
            self.w.options.progress.stop()
            self._resizeWindow(enlarge=True)
        
            time1 = time.time()
            print u'Touché: finished checking %d glyphs in %.2f seconds' % (glyphCount, time1-time0)
            
        else:
            Message(u'Touché: Can’t find a font to check.')
            
OpenWindow(ToucheTool)
