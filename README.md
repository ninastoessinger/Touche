# Touché 

A RoboFont extension to find touching/colliding glyph pairs.

**version 1.4**

Looking through your kerning, you try to catch them: _colliding glyph pairs_. But did you remember to check your i-diacritics against your superior numerals, ogoneks against brackets, the dcaron against the asterisk? Touché can take some guesswork out of things by listing the pairs whose black bodies touch, taking spacing and kerning into account.

![Touché Screenshot](/screenshot.png)

Touché makes no assumptions about the relevance of pairs, or which ones need fixing; and it does not change your data. Among the specified set of input glyphs, *Touché checks all of your glyphs against all of your glyphs*, lists and shows the touching pairs that it finds, and leaves the decision on whether and how to fix them up to you. The resulting pairs can be exported as a text file that can directly be used as a pair list in Metrics Machine. (It should go without saying that this can supplement and perhaps expedite, but in no way replace careful manual checking of kerning in general.) 

Version 1.2 includes a rewritten collision routine (thanks to Frederik Berlaen) that is much faster and more reliable than my previous version. Still, if you’re checking large numbers of glyphs, it can take a couple of minutes. You can also just check a subsection of glyphs, which should then be significantly faster.

Version 1.4 adds support for RoboFont 3 (Python 3 + FontParts) while still maintaining compatibility with RoboFont 1.8.
