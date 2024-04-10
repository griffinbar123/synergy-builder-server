import numpy as np
from sklearn.preprocessing import OneHotEncoder
import form_data
import fill_files
 
# fill_files.loadDataAndTargetsToCSV()

df, y = form_data.loadDataAndTargets()
print(df)
# X= df.to_numpy()

# ohe = OneHotEncoder(sparse_output=True)

# # print(df[])
# ne  = ohe.fit_transform(df[["tier"]])
# c = ohe.categories_

# print(ne, c)
