import re

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

data = requests.get('https://www.nutritionix.com/taco-bell/menu/premium?ajax=inmGrid&sort=calories')
soup = BeautifulSoup(data.content, "html.parser")

odd_cols = []
for span in soup.find_all('tr', class_="odd"):
    odd_cols += span

even_cols = []
for span in soup.find_all('tr', class_="even"):
    even_cols += span


def extract(cols):
    i = 0
    ls = []
    while i < len(cols):
        # find the title of the menu item
        if '<td class' in str(cols[i]):
            # the next 11 columns are the nutritional data for that item
            ls.append([re.findall('label="(.*?)"\sclass', str(cols[i+j]))[0] for j in range(1, 12)])
            ls[-1].append(re.findall('title="(.*?)"\>', str(cols[i]))[0])
        i += 1
    # Put name of item first in each sublist
    for k in range(len(ls)):
        ls[k] = ls[k][-1:] + ls[k][:-1]
    return ls


odd = extract(odd_cols)
even = extract(even_cols)

for ent in even:
    odd.append(ent)

col_names = ['Menu Item', 'Calories', 'Total Fat (g)', 'Saturated Fat (g)', 'Trans Fat (g)',
             'Cholesterol (mg)', 'Sodium (mg)', 'Carbohydrates (g)', 'Dietary Fiber (g)', 'Sugars (g)',
             'Added Sugars (g)', 'Protein (g)']


food = pd.DataFrame(odd)
food.columns = col_names


# clean data to keep only numerical string
def cleaner(value):
    if re.search('(\d*\.*,*\d+,*)', value):
        pos = re.search('(\d*\.*,*\d+,*)', value).end()
        return value[:pos]
    else:
        return value


for col in col_names[1:]:
    food[col] = food[col].apply(cleaner)


for col in col_names[1:]:
    for n in range(len(food[col])):
        # convert <# to 0
        if food[col][n] == '&lt;1' or food[col][n] == '&lt;5':
            food[col][n] = 0
        # remove comma from #'s
        if ',' in str(food[col][n]):
            food[col][n] = food[col][n].replace(',', '')


# Convert strings to float
for col in col_names[1:]:
    food[col] = food[col].astype('float')


# removing drinks
df = food[food["Menu Item"].str.contains("oz|proof|Water|Wine|Juice|Coffee|Creamer|Milk")==False]

df.to_csv('tbell_menu.csv', index=False)
