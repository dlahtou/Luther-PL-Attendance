import pandas as pd

with open('PLmatches.csv', 'r') as open_file:
    df = pd.read_csv(open_file, index_col=0)
 
print(df.info())
print(df.sort_values(by="home_fouls")['home_fouls'])