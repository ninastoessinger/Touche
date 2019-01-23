# coding=utf-8

from __future__ import print_function, absolute_import

from .touche import Touche

from vanilla import CheckBox, Group, List, ProgressSpinner, SquareButton, TextBox, Window
from mojo.UI import MultiLineView, OpenSpaceCenter
from mojo.roboFont import OpenWindow, CurrentFont, version

import time

if version > '2.0':
    from mojo.UI import PutFile, Message
else:
    from robofab.interface.all.dialogs import PutFile, Message

from io import open # see http://python-future.org/compatible_idioms.html#file-io-with-open

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
        for button, data in buttons.items():
            setattr(self.w.options, button,
            SquareButton((p, data["y"], w, 40), data["text"], callback=data["callback"], sizeStyle="small"))

        self.w.options.zeroCheck = CheckBox((p, 108, w, 20), "Ignore zero-width glyphs", value=True, sizeStyle="small")
        self.w.options.progress = ProgressSpinner((82, 174, 16, 16), sizeStyle="small")

        # results
        self.w.results = Group((0, 220, 180, -0))
        self.w.results.show(False)

        textBoxes = {"stats": 24, "result": 42}
        for box, y in textBoxes.items():
            setattr(self.w.results, box, TextBox((p, y, w, 14), "", sizeStyle="small"))

        moreButtons = {
            "spaceView": {"text": "View all in Space Center", "callback": self.showAllPairs, "y": 65},
            "exportTxt": {"text": "Export as MM pair list", "callback": self.exportPairList, "y": 90}}
        for button, data in moreButtons.items():
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
        path = PutFile(message="Choose save location", fileName="TouchingPairs.txt")
        if path is not None:
            reportString = "#KPL:P: TouchingPairs\n"
            for g1, g2 in self.touchingPairs:
                reportString += "%s %s\n" % (g1, g2)
            with open(path,'w+') as fi:
                try:
                    fi.write(reportString)
                except: #py2!
                    fi.write(unicode(reportString))

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
            bounds = g.bounds if version > '2.0' else g.box
            if bounds is not None and self._hasSufficientWidth(g):
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
            print(u'Touché: finished checking %d glyphs in %.2f seconds' % (len(glyphList), time1-time0))

        else:
            Message(u'Touché: Can’t find a font to check')
