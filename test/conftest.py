import sys
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "app")

sys.path.insert(0, os.path.join(BASE, "api", "v1", "learn_words"))
sys.path.insert(0, os.path.join(BASE, "utils"))  # app/utils/utils.py が learn_words/utils/ より優先
