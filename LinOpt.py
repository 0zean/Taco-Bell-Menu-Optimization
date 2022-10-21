import streamlit as st
import pandas as pd
from pulp import *
import matplotlib.pyplot as plt
import circlify
import random

st.title("Taco Bell Healthy Items Tool")
st.text('''
        This tool, inspired by Avery Smith's McDonalds tool,
        uses linear optimization to find possible orders
        that meet nutritional constraints given by the user.
        ''')

tbell = pd.read_csv('tbell_menu.csv')

MenuItems = tbell['Menu Item'].tolist()

# Convert all of the macro nutrients fields to be dictionaries of the item names
Calories = tbell.set_index('Menu Item')['Calories'].to_dict()
TotalFat = tbell.set_index('Menu Item')['Total Fat (g)'].to_dict()
SaturatedFat = tbell.set_index('Menu Item')['Saturated Fat (g)'].to_dict()
Carbohydrates = tbell.set_index('Menu Item')['Carbohydrates (g)'].to_dict()
Sugars = tbell.set_index('Menu Item')['Sugars (g)'].to_dict()
Protein = tbell.set_index('Menu Item')['Protein (g)'].to_dict()
Sodium = tbell.set_index('Menu Item')['Sodium (mg)'].to_dict()

prob = LpProblem('Tbell Optimization', LpMinimize)

MenuItems_vars = LpVariable.dicts("MenuItems", MenuItems, lowBound=0, upBound=15, cat='Integer')


st.sidebar.write('Limits for Combo')
TotalFat_val = st.sidebar.number_input('Total Fat Max', value=70)
SatFat_val = st.sidebar.number_input('Saturated Fat Max', value=20)

SugarMin = st.sidebar.number_input('Sugar Min', value=80)
SugarMax = st.sidebar.number_input('Sugar Max', value=100)

CarbsMin = st.sidebar.number_input('Carbohydrates Min', value=260)

ProteinMin = st.sidebar.number_input('Protein Min', value=45)
ProteinMax = st.sidebar.number_input('Protein Max', value=85)

SodiumMax = st.sidebar.number_input('Sodium Max', value=10)


# First entry is the calorie calculation (this is our objective)
prob += lpSum([Calories[i]*MenuItems_vars[i] for i in MenuItems]), "Calories"
# Total Fat must be <= 70 g
prob += lpSum([TotalFat[i]*MenuItems_vars[i] for i in MenuItems]) <= TotalFat_val, "TotalFat"
# Saturated Fat is <= 20 g
prob += lpSum([SaturatedFat[i]*MenuItems_vars[i] for i in MenuItems]) <= SatFat_val, "Saturated Fat"
# Carbohydrates must be more than 260 g
prob += lpSum([Carbohydrates[i]*MenuItems_vars[i] for i in MenuItems]) >= CarbsMin, "Carbohydrates_lower"
# Sugar between 80-100 g
prob += lpSum([Sugars[i]*MenuItems_vars[i] for i in MenuItems]) >= SugarMin, "Sugars_lower"
prob += lpSum([Sugars[i]*MenuItems_vars[i] for i in MenuItems]) <= SugarMax, "Sugars_upper"
# Protein between 45-55g
prob += lpSum([Protein[i]*MenuItems_vars[i] for i in MenuItems]) >= ProteinMin, "Protein_lower"
prob += lpSum([Protein[i]*MenuItems_vars[i] for i in MenuItems]) <= ProteinMax, "Protein_upper"
# Sodium <= 6000 mg
prob += lpSum([Sodium[i]*MenuItems_vars[i] for i in MenuItems]) <= SodiumMax*1000, "Sodium"


prob.solve()

# Loop over constraint set to get final solution
results = {}
for constraint in prob.constraints:
    s = 0
    for var, coefficient in prob.constraints[constraint].items():
        s += var.varValue * coefficient
    results[prob.constraints[constraint].name.replace('_lower','').replace('_upper','')] = s

objective_function_value = value(prob.objective)

varsdict = {}
for v in prob.variables():
    if v.varValue > 0:
        varsdict[v.name] = v.varValue
df_results = pd.DataFrame([varsdict])


st.header('Total Calories: ' + str(objective_function_value))


fig, ax = plt.subplots(figsize=(15, 10))
ax.set_title('Taco Bell Combo')
ax.axis('off')

circles = circlify.circlify(varsdict.values(),
                            show_enclosure=False,
                            target_enclosure=circlify.Circle(x=0,y=0,r=1))

# Axis boundaries
lim = max(max(abs(circle.x) + circle.r,
              abs(circle.y) + circle.r,)
          for circle in circles)

plt.xlim(-lim, lim)
plt.ylim(-lim, lim)

# labels list
labels = [i[10:] for i in varsdict.keys()]


for circle, label in zip(circles, labels):
    x, y, r = circle
    ax.add_patch(plt.Circle((x, y), r*0.7,
                            alpha=0.9,
                            linewidth=2,
                            facecolor="#%06x" % random.randint(0, 0xFFFFFF),
                            edgecolor="black"))

    plt.annotate(label, (x,y ) ,
                 va='center',
                 ha='center',
                 bbox=dict(facecolor='white',
                           edgecolor='black', boxstyle='round', pad=.5))

    value = circle.ex['datum']

    plt.annotate(value, (x,y-.1 ) ,
                 va='center',
                 ha='center',
                 bbox=dict(facecolor='white',
                           edgecolor='black', boxstyle='round', pad=.5))

st.pyplot(fig)

st.subheader('Created By Nicholas Picini')
st.caption('Get the code [here](https://github.com/0zean/Taco-Bell-Menu-Optimization)')
