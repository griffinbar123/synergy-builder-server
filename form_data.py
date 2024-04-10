import json
import sys

import numpy as np
import pandas as pd
import fill_files
# import pandas
# from enum import Enum




# print(getCleanChampionData("Zyra", "DIAMOND"))

def dataToArray(data):
    arr = []
    for k in data:
        l = data[k]
        if type(l) == str and l != "IRON" and l != "BRONZE" and l != "SILVER" and l != "GOLD" and l != "PLATINUM" and l != "EMERALD" and l != "DIAMOND":
            arr.append(float(data[k]))
        else:
            arr.append(data[k])
    return arr



def loadDataAndTargets():
    df = pd.read_csv("../../final_data.csv")
    # print(df)
    # X = df.loc[:, df.columns != 'win']
    df.columns.values[0] = "index"
    X = df.drop(['index','win'], axis=1)
    y = df["win"]
    return X, y.to_numpy()
# loadDataAndTargetsToCSV()



# print(X[206])
# print(y[206])


# print(dataToArray(getCleanChampionData("Zyra", "DIAMOND")))



# m = fill_files.load_matches(None, None)

# print(f"Total Matches: {len(m)}")
# print("Loading Match: ", end="")
# for index, m1 in enumerate(m):
#     if index == 1:
#         break
#     if index % 10500 == 0:
#         print(f"{index}, ", end="")
#         sys.stdout.flush()
#     # print(row['match_ids'], row['tier'])
#     print(matchToBetterObject(m1))