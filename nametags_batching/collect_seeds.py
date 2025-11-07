import os
import pandas as pd
''' Trawl through each seeds' results and find the best one'''
# ==== CONFIGURATION ====
Nmax = 5000               # change this to however many seeds you expect
nfinished=0
# ========================

data_rows = []
base_dirs=['data'] #where is the data stored
for base_dir in base_dirs: # where the seed_1, seed_2, ... folders live
    for n in range(1, Nmax + 1):
        seed_dir = os.path.join(base_dir, f"seed_{n}")
        results_path = os.path.join(seed_dir, "results.txt")
        
        if not os.path.exists(results_path):
            continue

        with open(results_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if len(lines) < 2:
            continue

        # First line has headers
        headers = lines[0].split()
        # Second line has values
        try:
            values = [float(x) for x in lines[1].split()]
        except ValueError:
            continue

        if len(headers) != len(values):
            continue

        row = dict(zip(headers, values))
        if base_dir == 'data': row["seed"] = n
        nfinished+=1
        data_rows.append(row)

# Convert to DataFrame for convenience
if data_rows:
    df = pd.DataFrame(data_rows)
    df = df.sort_values("seed").reset_index(drop=True)
    # print(df)
    
    filtered = df[(df["score1"] == df["total1"]) & (df["number_pissed_off"] == 0)] #the ones with no pissed off people and all guests adjacent to hosts
    # filtered = df[(df["score1"] == df["total1"])]
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):

        print(filtered)
        
        print(f'{len(filtered["score1"])} acccepted out of {nfinished}')

        filtered['ratio'] = filtered['score2'] / filtered['total2']  # compute the ratio
        best = filtered.loc[filtered['ratio'].idxmax()]               # pick row with max ratio

        best = filtered.loc[filtered['total_hapiness'].idxmax()]
        print('the best:')
        print(best)
