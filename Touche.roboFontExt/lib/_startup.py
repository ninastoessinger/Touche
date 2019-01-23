import sys
import os

path = os.path.dirname(__file__)

print(path)

if not path in sys.path:
    sys.path.append(path)
