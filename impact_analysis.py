import pandas as pd
import numpy as np
from preprocess import read_media

file = "saved_data/filtered_data_20250428_194522.csv"
df = read_media(file)
print(df)