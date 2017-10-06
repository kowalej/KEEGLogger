import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.DataFrame.from_csv("session data/jeb/PIN_FIXED_4/jeb_PIN_FIXED_4_2017-10-05-18꞉41꞉27_2017-10-05-18꞉44꞉34_EEG.csv")

matplotlib.style.use('ggplot')

df.plot()