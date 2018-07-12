import pandas as pd

with open('PLmatches.csv', 'r') as open_file:
    df = pd.read_csv(open_file, index_col=0)

print(df['home_goals'])
print(df.info())