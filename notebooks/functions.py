import pandas as pd
import numpy as np
import re

def parse_price(text: str) -> float:
    if pd.isna(text):
        return np.nan
    s = str(text).lower().strip().replace(',', ' ')
    m = re.match(r'([0-9]*\.?[0-9]+)\s*(crore|cr|million|m|lakh|lac|thousand|k)?', s)
    if not m:
        return np.nan
    val = float(m.group(1))
    unit = m.group(2)
    if unit in ('crore','cr'):
        val *= 1e7
    elif unit in ('million','m'):
        val *= 1e6
    elif unit in ('lakh','lac'):
        val *= 1e5
    elif unit in ('thousand','k'):
        val *= 1e3
    return val
