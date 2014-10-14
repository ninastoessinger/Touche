def findPointOnLine(pt1, pt2, p):
    """ 
    Find if the point p is on the line between pt1 and pt2.
    This is derived from fontTools.misc.bezierTools.splitLine()
    """
    p1x, p1y = pt1
    p2x, p2y = pt2
    px, py = p

    ax, ay = (p2x - p1x), (p2y - p1y)
    bx, by = p1x, p1y
    
    if ax == 0:
        # would cause a division by zero below; handle separately
        if px == p1x:
            if p2y > py > p1y:
                return True
            elif p1y > py > p2y:
                return True
        return False

    t = (px - bx) / ax
    if 0 <= t < 1:
        midPt = ax * t + bx, ay * t + by
        if midPt[1] == py:
            return True
    return False
    
