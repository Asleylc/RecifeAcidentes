import pandas as pd
import csv
import googlemaps
import json
import io
import unicodedata
import numpy as np

# importa os dados

#
# arquivo = open('acidentes-transito-2017-2019.csv')
#
# linhas = csv.reader(arquivo)
# l = []
# for i, linha in enumerate(linhas):
#     print(linha)
#     if i == 0:
#         head = linha[0].split(';')
#     else:
#         try:
#             if len(linha[0].split(';')) == 18:
#                 l.append(linha[0].split(';'))
#         except:
#             pass
#
# df = pd.DataFrame(data=l, columns=head)


df = pd.read_csv('acidentes-transito-2017-2019.csv', sep=';', encoding='latin-1')
df['local'] = df['endereco'] + ', RECIFE, BRASIL'

#Recuperar coordenadas

gmaps = googlemaps.Client(key='coloque sua chave')

# Geocoding an address
lat_dict = {}
lng_dict = {}
for s in df['local'].unique():
    try:
        geocode_result = gmaps.geocode(s)
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        lat_dict[s] = lat
        lng_dict[s] = lng
        print('Correto')
    except:
        print(s)
        lat_dict[s] = 0
        lng_dict[s] = 0

# add coordenadas

df['lat']= df['local'].map(lat_dict)
df['lng']= df['local'].map(lng_dict)
df = df.drop(df.loc[df['lat']==0, 'local'].index)

# funcao para trasformar as multiplas colunas em uma só
def get_only(df, first_column, second_column=""):
    if second_column == "":
        columns = ['auto', 'moto', 'ciclom', 'ciclista', 'pedestre', 'onibus', 'caminhao', 'viatura']
        columns = [x for x in columns if x != first_column]
        only = df[columns] != 0
        only = (only.sum(axis=1) == 0) & (df[first_column] != 0)
        df.loc[only,'acidentes']  = first_column
    else:
        columns = ['auto', 'moto', 'ciclom', 'ciclista', 'pedestre', 'onibus', 'caminhao', 'viatura']
        columns = [x for x in columns if x != first_column and x != second_column]
        only = df[columns] != 0
        only = (only.sum(axis=1) == 0) & (df[first_column] != 0) & (df[second_column] != 0)
        df.loc[only,'acidentes']  = first_column + "_" + second_column
    return only

# Corrigindo os dados
#Corrigindo os dados de texto
def correct_test(x):
    if x != np.nan:
        x=x.replace('Err:512', 'OUTROS')
        x=x.replace('0', 'OUTROS')
        x=x.replace('Ã\x8d', 'I')
        x=x.replace('\x83', '')
        x=x.replace('Ã', 'A')
        x=x.replace('A\x87', 'C')
        x = x.replace('\x81', '')
        x = x.replace('Ô', '')
        remove_accents(x)
    return x.upper()

# removendo acento
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

for c in ['tipo', 'situacao', 'natureza', 'descricao', 'local']:
    df[c] = df[c].fillna('OUTROS')
    df[c] = df[c].apply(lambda x: correct_test(x))

# tratando os dados numéricos
for c in ['auto', 'moto', 'ciclom', 'ciclista', 'pedestre', 'onibus', 'caminhao', 'viatura']:
    df[c] = df[c].fillna(0)

# constroe coluna de acidentes
df['acidentes'] = 'outros'
only_auto = get_only(df, 'auto')
only_moto = get_only(df, 'moto')
only_onibus = get_only(df, 'onibus')
only_caminhao = get_only(df, 'caminhao')

only_auto_moto = get_only(df, 'auto', 'moto')
only_auto_onibus = get_only(df, 'auto', 'onibus')
only_auto_caminhao = get_only(df, 'auto','caminhao')

df['acidentes'] = df['acidentes'].apply(lambda x: correct_test(x))


# funcao para transformar em inteiro
def make_int(x):
    try:
        result = int(x)
    except:
        result = 0
    return result

#coluna auxiliar de vitimas['nenhuma', 'vitimas','vitimasfatais']
df['vitimas'] = df['vitimas'].apply(lambda x: make_int(x))
df['vitimasfatais'] = df['vitimasfatais'].apply(lambda x: make_int(x))
df['tipo_vitima'] = 'SEM VITIMAS'
df['tipo_vitima'] = df['tipo_vitima'].apply(lambda x: correct_test(x))


df.loc[df['vitimas'] > 0, 'tipo_vitima'] = 'VITIMAS'
df.loc[df['vitimasfatais'] > 0, 'tipo_vitima'] = 'VITIMAS'
df['n_vitimas'] = df['vitimas'] + df['vitimasfatais']

# numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']

# newdf = df.select_dtypes(include=numerics).columns

for c in ['auto', 'moto', 'ciclom', 'ciclista', 'pedestre', 'onibus', 'caminhao',
       'viatura', 'vitimas', 'vitimasfatais', 'n_vitimas',
       'envolvidos']:
    df[c] = df[c].astype(int)

# construindo coluna de tempo correta
df = df.loc[df['hora'].dropna().index]
df['data_completa'] = df['data'] + "-" + df['hora']
df['data_completa'] = df['data_completa'].apply(lambda x: x + ':00' if len(x)< 19 else x)
# Construindo coluna total de envolvidos
df['envolvidos'] = df[['auto', 'moto', 'ciclom', 'ciclista', 'pedestre', 'onibus', 'caminhao', 'viatura']].sum(axis=1)

# Removendo linhas estranhas
df = df.drop(df.loc[df['data_completa'] == "13/04/2018-M:00"].index)
df = df.drop(df.loc[df['data_completa'] == "26/04/2018-MARINALVA"].index)
df = df.drop(df.loc[df['data_completa'] == "28/05/2018-07;05:00"].index)



# salva os dados
df.to_csv('dados_acidentes_tratados.csv', sep=';')
# colunas selecionadas para o json -8.3781832 lng: -35.2451693
data = df.loc[((-35.2<=df['lng']) & (df['lng']<=-34.87021841)) & ((-8.37 <=df['lat']) &(df['lat']<=-7.9548252))]
data = data[['tipo','situacao', 'data_completa', 'natureza', 'descricao', 'n_vitimas', 'tipo_vitima', 'local', 'lat', 'lng', 'acidentes', 'envolvidos']]
data = data.dropna(axis=1)
data = data.to_dict('records')
#salva o json

with open('acidentes_2019.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)



