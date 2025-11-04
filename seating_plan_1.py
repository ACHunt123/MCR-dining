import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy.linalg import block_diag
from matplotlib.widgets import Button
from setup import get_Matrices,plot_setup
from metrics_moves import total_happiness,all_happiness,swap_seats,all_sat_with_guests
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
# s0=np.arange(ntot)
# p0=np.arange(ntot)
# Random permutation for seating


### Randomize initial confign
# Set a different seed, e.g., 42
np.random.seed(42)
s0 = np.random.permutation(ntot)
p0 = np.empty_like(s0)
p0[s0] = np.arange(ntot)
h0=total_happiness(A,P,G,p0,s0)

### Setup the plot
show=0
save_to_spreadsheet=1
if show:
    sc,ax,stop_button,text_labels=plot_setup(plt,seat_positions,all_happiness(A,P,G,p0,s0),p0)
    def stop(event):sys.exit()
    stop_button.on_clicked(stop)
T=10
nt=10000
for it in range(nt):  
    T*=0.9995

    i, j = np.random.choice(ntot, size=2, replace=False)
    s,p=swap_seats(i,j,s0.copy(),p0.copy())
    h=total_happiness(A,P,G,p,s)

    delta_h = h - h0
    if it%100==0:
        all_sat_with_guests(s,A,guestlist)
        print(f'{it}/{nt}   h={h}   T={T}')
        if show:
            ax.set_title(f"Update {it+1}")
            plt.draw()
            plt.pause(0.00001)  # wait 5 seconds

    # Always accept if better, otherwise accept with probability exp(delta_h / T)
    if delta_h > 0 or np.random.rand() < np.exp(delta_h / T):
        h0=h
        s0=s.copy()
        p0=p.copy()
        if show:
            sc.set_array(all_happiness(A,P,G,p,s))                   # update scatter color data
            for seat_idx, t in enumerate(text_labels): #update 
                t.set_text(p[seat_idx])  # 

    
## Save the results to the seating plan
import openpyxl
filename= f'data/Seating-plan-template.xlsx'
wb = openpyxl.load_workbook(filename)
ws = wb.active 
# Write each name into its corresponding cell
for (col, row), person_indx in zip(seat_positions, p):
    name=namelist[person_indx]
    # print(row,col)
    ws.cell(row=int(row), column=int(col), value=name)

# Save under a new name to keep the original template safe
wb.save(f"data/seating_filled.xlsx")
# save as a pdf
df = pd.read_excel(f"data/seating_filled.xlsx", sheet_name="Sheet1")
df = df.fillna('')
html = df.to_html(index=False, border=1, justify='center')
with open("table.html", "w") as f:
    f.write(html)
from weasyprint import HTML
HTML("table.html").write_pdf("seating_chart.pdf")




if show:
    plt.ioff()  # turn off interactive mode when done
    plt.show()



