import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy.linalg import block_diag
from matplotlib.widgets import Button
from getnames import AttendeeScraper

### Get the names from Upay
filename = "/mnt/c/Users/Cole/Downloads/Upay - Event Booking.html"
guestlist=AttendeeScraper(filename)
guestlist.load_html()
guestlist.get_attendees()
# print(guestlist.everyone)


# Read the Excel file into a DataFrame
file_path = "/mnt/c/Users/Cole/Downloads/Superhall Seating Request Form (Responses).xlsx"
df = pd.read_excel(file_path, engine='openpyxl')

'''
Calculate the seating plan using Monte Carlo.
A: adjacency matrix [seats->seats]         Gives score of how good seating is. e.g. A12 = how good is it for 1 to sit with 2
P: preference matrix [people->people]      Gives people's preference of sitting next to eachother. e.g. P23 = how person 2 rated 3
T: transformation matrix [people->seats]   Stores the position of each person (binary choice)
G: gallery matrix [people->seats]          Stores preferences of people to be in gallery. Also if needed can add biasing for seats to be at end of table

The most difficult is to get the A matrix from the Geomety of the hall (difficult as hell).

There are two types of tables, some long, and some square (in gallery)

We assume that separate tables have no adjacent seats. This makes the problem block-diagonal (YAY)

We number the tables from top left (north is high-table) anticlockwise, starting from left most table. First hall, then gallery
'''
npl=len(guestlist.everyone)
nsts=120
# Get the A matrix

### Setup the Hall (three long tables and 2 square in the gallery)
table_types=['long','long','long','square','square']
center_posns=np.array([[0,0],[3,0],[6,0],[1,-12],[4,-12]])
widths=[1,1,1,2,2]
table_seats=[30,30,30,12,12]
A=np.array([])

def A_blk(table_type,nsts,center_posn=np.array([0,0]),length=10,width=1):
    seat_positions=np.zeros((nsts,2))
    A_block=np.zeros((nsts,nsts))
    if table_type=='long':
        assert nsts%2==0,'number of seats on table must be even'
        l_indices=np.arange(0,nsts//2)
        r_indices=np.arange(nsts//2,nsts)

        delta_height=length/(nsts//2)
        for i, (l_indx,r_indx) in enumerate(zip(l_indices,r_indices)):
            ### assign the seat positions
            seat_positions[l_indx,:] = center_posn - (width/2)*np.array([1,0]) - i*delta_height*np.array([0,1])
            seat_positions[r_indx,:] = center_posn + (width/2)*np.array([1,0]) - i*delta_height*np.array([0,1])
            ### weights
            w_opposite=3
            w_adjacent=2
            w_diagonal=1
            # across from eachother
            A_block[l_indx,r_indx]=A_block[r_indx,l_indx]=w_opposite 
            # next to eachother and diagonals
            if l_indx+1 in l_indices:
                A_block[l_indx,l_indx+1]=A_block[l_indx+1,l_indx]=w_adjacent
                A_block[r_indx,l_indx+1]=A_block[l_indx+1,r_indx]=w_diagonal 
            if r_indx+1 in r_indices:
                A_block[r_indx,r_indx+1]=A_block[r_indx+1,r_indx]=w_adjacent
                A_block[l_indx,r_indx+1]=A_block[r_indx+1,l_indx]=w_diagonal
            if l_indx-1 in l_indices:
                A_block[l_indx,l_indx-1]=A_block[l_indx-1,l_indx]=w_adjacent
                A_block[r_indx,l_indx-1]=A_block[l_indx-1,r_indx]=w_diagonal
            if r_indx-1 in r_indices:
                A_block[r_indx,r_indx-1]=A_block[r_indx-1,r_indx]=w_adjacent
                A_block[l_indx,r_indx-1]=A_block[r_indx-1,l_indx]=w_diagonal
        return A_block,seat_positions
    elif table_type=='square':
        assert (nsts)%4==0,'number of seats on table must be 4n'
        n1side=(nsts)/4
        delta_sidelength=width/n1side
        seat_position=center_posn-(width/2)*np.array([1,1])
        directions=np.array([[0,-1],[1,0],[0,1],[-1,0]])

        indices=np.arange(0,nsts)
        for indx in indices:
            ### seat position
            seat_positions[indx,:] = seat_position
            seat_position+=directions[int(indx//n1side),:]*delta_sidelength
            ### weights
            w_adjacent1=3
            w_adjacent2=1

            # directly next to eachother 
            A_block[indx,(indx+1)%nsts]=A_block[(indx+1)%nsts,indx]=w_adjacent1
            # two away
            A_block[indx,(indx+2)%nsts]=A_block[(indx+2)%nsts,indx]=w_adjacent2
    return A_block, seat_positions

    
seat_positions=np.array([[None,None]])
gallery_seat_indices=np.array([])
i0=0
for table_type,center_posn,seats,width in zip(table_types,center_posns,table_seats,widths):
    A_i,seat_positions_i=A_blk(table_type,seats,center_posn=center_posn,width=width)
    seat_positions=np.concatenate([seat_positions,seat_positions_i])
    if table_type=='square':
        gallery_seat_indices=np.concatenate([gallery_seat_indices,np.arange(i0,i0+seats)])
    else:
        gallery_seat_indices=np.concatenate([gallery_seat_indices,np.arange(i0,i0+seats)*0])
    
    i0+=seats
    A=block_diag(A,A_i)
seat_positions=seat_positions[1:,:] # remove the nones that we put in
gallery_seat_indices = gallery_seat_indices.astype(int)
ntot=np.shape(A)[0]

# Get the P and G matrices from the seating form
A=np.zeros((npl,npl)); P=np.zeros((npl,npl)); T=np.zeros((npl,npl)); G=np.zeros((npl,npl))
for index, row in df.iterrows():# go through each row in the spreadsheet
    ## do the preferences for seating next to eachother
    name = row['What is your name ?']
    name_indx=guestlist.find(name)
    prefs_indx = np.empty(3)
    prefs_weights=[3,2,1] # weighting for the prefs
    for pl, priority_level in enumerate(['First','Second','Third']):
        pref = row[f'Who would you like to sit next to?  {priority_level} priority']
        if pd.isna(pref): continue # if the preference is not specified in the form continue
        # print(f'{priority_level} priority is {pref}')
        pref_indx=guestlist.find(pref) # find the index in the name list
        P[name_indx,pref_indx]=prefs_weights[pl] # assign the preferential weight
    ## do the preferences for sitting in the gallery
    gallery_pref = row['I would prefer to be seated in the Gallery ']
    gallery_weight=5 # weighting for sitting in gallery
    if gallery_pref=='Yes':
        print(gallery_seat_indices)
        G[name_indx,gallery_seat_indices]=gallery_weight

### Setup the plot
plt.ion()
fig, ax = plt.subplots()
ns=np.arange(0,ntot-1)
sc = ax.scatter([x for x,y in seat_positions],[y for x,y in seat_positions],  c=gallery_seat_indices, cmap='RdYlGn')
plt.colorbar(sc,label='n value')
# Button setup
button_ax = plt.axes([0.4, 0.05, 0.2, 0.075])  # x, y, width, height
stop_button = Button(button_ax, 'STOP', color='lightcoral', hovercolor='red')
def stop(event):
    sys.exit()
stop_button.on_clicked(stop)

# Loop that updates colors every 5 seconds
for i in range(1000):  # update 10 times
    # ns = np.random.rand(ntot) * 100  # new color values
    # sc.set_array(ns)  # update scatter color data
    ax.set_title(f"Update {i+1}")
    plt.draw()
    plt.pause(6)  # wait 5 seconds

plt.ioff()  # turn off interactive mode when done
plt.show()


# Setup the tables
# names 
# priority [p1,p2,p3]


# Display the first few rows
# print(df.head())
