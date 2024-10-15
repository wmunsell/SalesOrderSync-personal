import pandas as pd

# read the Cabentry Item Data Import Master.xlsx file 
# and create a dictionary with the SKU as the key

def generate_dict():
    df = pd.read_excel('Cabentry Item Data Import Master.xlsx')
    df = df[['SKU', 'Type']]
    df = df.dropna()
    df = df.set_index('SKU')
    # return a list of unique values in the 'Type' column
    return df.to_dict()['Type']

# print a unique list of values in the 'Type' column
types = generate_dict()
unique = set(types.values())
for value in unique:
    print(value)

