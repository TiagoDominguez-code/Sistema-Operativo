import pandas as pd

df  = pd.read_csv('probando2.csv')

#print(df.loc[0,'Nombre'])
'''
nuevo_nombre = pd.DataFrame ([{
    'Nombre': 'tiago',
    'Edad': 20,
    'Ciudad': 'Corrientes',




}]) 

nuevo_nombre.to_csv('probando2.csv',mode='a',header=False, index=False)
''' 
df = df[df['Nombre'] != 'ramon']



#print (len(df))
df.index = range(1,len(df)+1)

df.to_csv('probando2.csv', index=False)

print (df)
