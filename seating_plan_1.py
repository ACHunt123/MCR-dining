import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy.linalg import block_diag
from matplotlib.widgets import Button
from setup import get_Matrices,plot_setup
from metrics_moves import total_happiness,all_happiness,trial_move,trial_move2,all_sat_with_guests,all_sat_with_friends

import argparse
import numpy as np

# Add argparse
parser = argparse.ArgumentParser(description="Run seating / bath simulation with optional seed")
parser.add_argument("--seed", type=int, default=None, help="Random seed")
args = parser.parse_args()

# Set the seed if provided
if args.seed is not None:
    np.random.seed(args.seed)
    import random
    random.seed(args.seed)
    print(f'using seed {args.seed}')


folder='/mnt/c/Users/Cole/Downloads'
folder='/home/colehunt/software/MCR-dining/data'
folder='/home/ach221/Downloads'
### Get the names from Upay and seating form responses to generate the Matrices required
event_booking_html = f"{folder}/Upay - Event Booking.html"
seating_form_responses = f"{folder}/Superhall Seating Request Form (Responses).xlsx"
swaps_xls = f"{folder}/MTSuperhallSwaps2025-26.xlsx"
A,P,G,seat_positions,guestlist = get_Matrices(event_booking_html,swaps_xls,seating_form_responses) #matrices in csr format
namelist=guestlist.everyone
ntot=A.shape[0]
print(f'total number of seate {ntot}')
'''
Calculate the seating plan using Monte Carlo.
A: adjacency matrix     A[seat#,:]= list of weights on seat#s      Gives score of how good seating is. e.g. A12 = how good is it for 1 to sit with 2
P: preference matrix    P[person#,:]= list of that person's preference on person#s
G: gallery matrix       G[person#,:]= list of person's prefrence on seat#s
s: Seat location        s[person#]= seat#   
p: Person location      p[seat#]= person#   
'''



### Initial conditions
# s=np.arange(ntot)
# p=np.arange(ntot)
# Random permutation for seating


### Randomize initial confign
# Set a different seed, e.g., 42
np.random.seed(788)
s = np.random.permutation(ntot)
p = np.empty_like(s)
p[s] = np.arange(ntot)
h=total_happiness(A,P,G,p,s)

### Setup the plot
show=0
save_to_spreadsheet=1
if show:
    sc,ax,stop_button,text_labels=plot_setup(plt,seat_positions,all_happiness(A,P,G,p,s),p)
    def stop(event):sys.exit()
    stop_button.on_clicked(stop)
        
T = 10
hlist = []
nt = 1_000_00
cooling_rate = 0.9995
nhist = 50
tol = 0.1
h_best=0
p_best=p.copy()
h = total_happiness(A, P, G, p, s)
h0=h

for it in range(nt):
    # pick two random people to swap
    # i, j = np.random.choice(ntot, size=2, replace=False)
    # s_trial, p_trial = swap_seats(i, j, s.copy(), p.copy())
    # h_trial = total_happiness(A, P, G, p_trial, s_trial)
    # delta_h = h_trial - h
    delta_h,s_trial,p_trial=trial_move2(ntot,s,p,A,P,G)

    # Metropolis acceptance rule
    if delta_h > 0 or np.random.rand() < np.exp(delta_h / T):

        h += delta_h
        s[:] = s_trial
        p[:] = p_trial

    # Every 100 steps, monitor progress
    if it % 500 == 0:
        score1,total1=all_sat_with_guests(s,A,guestlist)
        print('SCORE1: {} of {}'.format(score1,total1))
        print(all_sat_with_friends(s,A,P,guestlist)[0])

        print(f'{it}/{nt}   h={h:.2f}   T={T:.3f}')
        hlist.append(h)

            # Store best configuration if new better one here

        if show:
            ax.set_title(f"Update {it+1}")
            plt.draw()
            plt.pause(0.00001)

    # Check for local minimum (every 1000 steps maybe)
    if len(hlist) >= nhist and it % 1000 == 0:
        recent = np.array(hlist[-nhist:])
        mean = np.mean(recent)
        var = np.var(recent) / (mean**2 + 1e-9)
        if var < tol:
            print(f"🔥 Local minimum detected at iteration {it}. Reheating!")
            T *= 10   # reheat
            hlist = []  # reset history

    # Gradual cooling
    T *= cooling_rate

    if h>h_best:# and score1==total1:
        h_best=h
        p_best=p.copy()
        s_best=s.copy()    
## Save the results to the seating plan
import openpyxl
print(f'best happiness {h_best}')
script_path='/home/ach221/software/MCR-Dining'
filename= f'{script_path}/data/Seating-plan-template.xlsx'
wb = openpyxl.load_workbook(filename)
ws = wb.active 
# Write each name into its corresponding cell
for (col, row), person_indx in zip(seat_positions, p_best):
    name=namelist[person_indx]
    # print(row,col)
    ws.cell(row=int(row), column=int(col), value=name)

# Save under a new name to keep the original template safe
wb.save(f"seating_filled.xlsx")
score1,total1=all_sat_with_guests(s,A,guestlist)
outstr,npissed,score2,total2=all_sat_with_friends(s,A,P,guestlist)

data = np.array([[score1, total1,score2,total2, npissed]])

# Save numeric data
np.savetxt("results.txt", data, 
           header="score1 total1 score2 total2 number_pissed_off", 
           fmt="%.4f", 
           comments="")



if show:
    plt.ioff()  # turn off interactive mode when done
    plt.show()



