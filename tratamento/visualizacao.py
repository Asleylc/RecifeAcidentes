import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('dados_acidentes_tratados.csv', sep=';',index_col=0)

df = df[['tipo', 'situacao', 'data', 'natureza', 'descricao', 'n_vitimas', 'tipo_vitima', 'local', 'lat', 'lng', 'acidentes']]


plt.hist(df['tipo_vitima'], normed=True, alpha=0.5)
plt.show()

plt.bar(df['acidentes'], height=1200)
plt.show()

plt.hist(df['tipo'], normed=True, alpha=0.5)
plt.show()