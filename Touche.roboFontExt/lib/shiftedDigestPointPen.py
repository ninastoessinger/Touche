from robofab.pens.digestPen import DigestPointPen


class ShiftedDigestPointPen(DigestPointPen):
    """ 
    Accepts a tuple that it adds to all the returned point coordinates, as though the glyph were shifted. 
    Also allows outputting of a digest that only contains on-curve points. Skips components.
    """
    
    def __init__(self, shift=(0, 0)):
        DigestPointPen.__init__(self, ignoreSmoothAndName=True)
        self.shift = shift
        
    def addPoint(self, pt, segmentType=None, **kwargs):
        pt = tuple([x + y for x, y in zip(pt, self.shift)])
        self._data.append((pt, segmentType))
        
    def addComponent(self, baseGlyphName, transformation):
        pass
        
    def getPointDigest(self, onCurveOnly=True):
        points = []
        from types import TupleType
        for item in self._data:
            if type(item) == TupleType:
                if onCurveOnly:
                    if item[1] is None:
                        continue
                points.append(item)
        points.sort()
        return tuple(points)
            
            
            
            
            
   