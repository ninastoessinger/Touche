Looking through your kerning, you try to catch them: _colliding glyph pairs_. But did you remember to check your i-diacritics against your superior numerals, ogoneks against brackets, the dcaron against the asterisk? Touché can take some guesswork out of things by programmatically listing pairs whose black bodies touch.

![Touché Screenshot](/screenshot.png)

Touché makes no assumptions about the relevance of pairs; and it does not change your data. Among the specified set of input glyphs, *Touché checks all of your glyphs against all of your glyphs*, lists and shows the touching pairs that it finds, and leaves the decision on whether and how to fix them up to you. The resulting pairs can be exported as a text file that can directly be used as a pair list in Metrics Machine. (It should go without saying that this can supplement and perhaps expedite, but in no way replace careful manual checking of kerning in general.) 

In this very first version, there are probably bugs I haven’t caught and cases that may not be evaluating correctly yet; reports welcome. Please be aware that if you’re checking large numbers of glyphs, it will take some time: on my MacBook Pro, checking an entire font of around 500 glyphs is taking anywhere between 40 seconds and a few minutes. You can also just check a subsection of glyphs, which should then be significantly faster. I hope to improve performance over time; meanwhile, if it frustrates you too much, just think how impossibly long it would take to check everything against everything, manually. :-)

Notes:
- Only tested with cubic curves.
- No guarantees that it will catch everything; some more finicky/theoretical edge cases have not been covered yet (there are some comments in the code).

