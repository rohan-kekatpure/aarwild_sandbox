import pandas as pd

base = pd.read_csv('layout_base.csv', usecols=[0, 1])
gray = pd.read_csv('layout_grayscale.csv', usecols=[0, 1])
eroded = pd.read_csv('layout_eroded.csv', usecols=[0, 1])

combined = pd.merge(base, gray, on='img', suffixes=['_base', '_gray'])
combined = pd.merge(combined, eroded, on='img')
combined.rename(columns={'good': 'good_eroded'}, inplace=True)
combined.sort_values(by='img', inplace=True)
combined.to_csv('./layout_results.csv', header=True, index=False)

