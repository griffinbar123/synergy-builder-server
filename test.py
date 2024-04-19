import sys
from joblib import dump, load
import json
import numpy as np



if len(sys.argv) == 2:
    input_data_js = json.loads(sys.argv[1])
    input_data = np.array(list(input_data_js.values()))
    tier = input_data[0]
    input_data = input_data[1:]
    # print(f"input data {input_data}")
    clf = load("./models/" + tier.upper() + '_gbc.joblib')
    input_data = input_data.reshape(1, -1)
    win = clf.predict(input_data)
    # print(win)
    # sys.stdout.flush()
    win_js = {"win" : win[0]}
    print(json.dumps(win_js, indent=4))
    sys.stdout.flush()
else:
    print(" ")
    sys.stdout.flush()
