import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy.linalg import block_diag
from matplotlib.widgets import Button
from getnames import AttendeeScraper
from scipy.sparse import csr_matrix


def get_Matrices(event_booking_html,swaps_xlsprd,seating_form_responses):
    ### Get the names from Upay
    guestlist=AttendeeScraper(event_booking_html,swaps_xlsprd)
    guestlist.load_Upay()
    guestlist.load_Swaps()
    # guestlist.pretty_print()
    

    # Read the Excel file of preferences in seating into a DataFrame
    df = pd.read_excel(seating_form_responses, engine='openpyxl')

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
    ### Setup the Hall (three long tables and 2 square in the gallery)
    table_types=['long','long','long','long','square','square']
    table_seats=[30,30,30,30,12,12]#144-120 =24
    table_types=['long','long','long','long']
    table_seats=[40,40,40,38]
    max_long_length=np.max(table_seats[0:4])//2
    posns=np.array([[3,6],[8,6],[13,6],[18,6],[6,31],[13,31]]) #cell position of the top left person
    def A_blk(table_type,nsts,posn=np.array([0,0]),length=10):
        seat_positions=np.zeros((nsts,2))
        A_block=np.zeros((nsts,nsts))
        if table_type=='long':
            assert nsts%2==0,'number of seats on table must be even'
            l_indices=np.arange(0,nsts//2)
            r_indices=np.arange(nsts//2,nsts)

            for i, (l_indx,r_indx) in enumerate(zip(l_indices,r_indices)):
                ### assign the seat positions
                seat_positions[l_indx,:] = posn + i*np.array([0,1])
                seat_positions[r_indx,:] = posn + np.array([2,0])+ i*np.array([0,1])
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
            directions=np.array([[0,1],[1,0],[0,-1],[-1,0]])

            indices=np.arange(0,nsts)
            seat_position=posn.copy()
            for indx in indices:
                if indx%n1side==0:                seat_position+=directions[int(indx//n1side),:]

                ### seat position
                seat_positions[indx,:] = seat_position
                seat_position+=directions[int(indx//n1side),:]
                ### weights
                w_adjacent1=3
                w_adjacent2=1

                # directly next to eachother 
                A_block[indx,(indx+1)%nsts]=A_block[(indx+1)%nsts,indx]=w_adjacent1
                # two away
                A_block[indx,(indx+2)%nsts]=A_block[(indx+2)%nsts,indx]=w_adjacent2
        return A_block, seat_positions
    ### Put the seat positions and Adjacency matrices together    
    A=None
    seat_positions=None
    gallery_seat_indices=None
    i0=0
    for table_type,posn,seats in zip(table_types,posns,table_seats):
        A_i,seat_positions_i=A_blk(table_type,seats,posn=posn)
        seat_positions=np.concatenate([seat_positions,seat_positions_i]) if seat_positions is not None else seat_positions_i
        if table_type=='square': # get the indices of the gallery seats
            gallery_seat_indices=np.concatenate([gallery_seat_indices,np.arange(i0,i0+seats)]) if gallery_seat_indices is not None else np.arange(i0,i0+seats)
        else:
            gallery_seat_indices=np.concatenate([gallery_seat_indices,np.arange(i0,i0+seats)*0]) if gallery_seat_indices is not None else np.arange(i0,i0+seats)*0
        i0+=seats
        A=block_diag(A,A_i) if A is not None else A_i
    gallery_seat_indices = gallery_seat_indices.astype(int)

    # Get the P and G matrices from the seating form
    P=np.zeros_like(A); G=np.zeros_like(A)
    for index, row in df.iterrows():# go through each row in the spreadsheet
        ## do the preferences for seating next to eachother
        name = row['What is your name ?']
        Qs=['Who would you like to sit next to?  First priority. You will automatically be put with your guests.',
            'Who would you like to sit next to?  Second priority.  You will automatically be put with your guests.',
            'Who would you like to sit next to?  Third priority. You will automatically be put with your guests!!',]
        name_indx=guestlist.find(name)
        if name_indx==-1:
            print(f'name {name} in superhall preference form not found')
        prefs_weights=[3,2,1] # weighting for the prefs
        for pl, Question in enumerate(Qs):
            pref = row[Question]
            if pd.isna(pref): continue # if the preference is not specified in the form continue
            # print(f'{priority_level} priority is {pref}')
            pref_indx=guestlist.find(pref) # find the index in the name list
            if pref_indx==-1:
                print(f'preference of {pref} not found in guestlist, skipping')
                continue
            P[name_indx,pref_indx]+=prefs_weights[pl] # assign the preferential weight
        ## do the preferences for sitting in the gallery
        gallery_pref = row['I would prefer to be seated in the gallery if it is to be open']
        gallery_weight=5 # weighting for sitting in gallery
        if gallery_pref=='Yes':
            G[name_indx,gallery_seat_indices]=gallery_weight
    
    # Add preferences for sitting next to your guests
    guest_pref=10
    print(f'total number of people: {len(guestlist.everyone)}')

    for attendee in guestlist.attendees:

        attendee_indx=guestlist.find(attendee)
        if attendee_indx==-1: 
            print(f'attendee {attendee} not found')
            continue

        for guest in guestlist.attendees_guest_map[attendee]:
            guest_indx=guestlist.find(guest)
            if guest_indx==-1:
                print(f'guest {guest} not found')
                continue

            P[guest_indx,attendee_indx]+=guest_pref
            P[attendee_indx,guest_indx]+=guest_pref
            # print(f'attendee{attendee_indx}')
            # print(f'guest_indx{guest_indx}')
            # print(f'__{guest}')
            # sys.exit()
    
        
    return csr_matrix(A),csr_matrix(P),csr_matrix(G),seat_positions,guestlist
    # return A,P,G,seat_positions

def plot_setup(plt,seat_positions,happiness,p,mode='interactive'):
    ### Setup the plot
    if mode=='interactive':plt.ion()
    fig, ax = plt.subplots()
    ax.invert_yaxis() #for excel-like indexing
    sc = ax.scatter([x for x,y in seat_positions],[y for x,y in seat_positions],  c=happiness, cmap='RdYlGn')
    plt.colorbar(sc,label='n value')
    # Button setup
    button_ax = plt.axes([0.4, 0.05, 0.2, 0.075])  # x, y, width, height
    stop_button = Button(button_ax, 'STOP', color='lightcoral', hovercolor='red')
    text_labels = []
    for seat_number, (x, y) in enumerate(seat_positions):
        t = ax.text(x, y, p[seat_number], fontsize=9, ha='center', va='center', color='black')
        text_labels.append(t)
    return sc,ax,stop_button,text_labels

    

if __name__=='__main__':
    A,P,T,G,seat_positions = get_Matrices("/mnt/c/Users/Cole/Downloads/Upay - Event Booking.html",
        "/mnt/c/Users/Cole/Downloads/Superhall Seating Request Form (Responses).xlsx")
    ntot=A.shape[0]
    happiness=[int(i) for i in np.arange(0,ntot)]
    print(A.shape)
    print(seat_positions.shape)
    # print
    sc,ax,stop_button=plot_setup(plt,seat_positions,happiness)
    def stop(event):sys.exit()
    stop_button.on_clicked(stop)
    # Loop that updates colors every 5 seconds
    for i in range(1000):  # update 10 times
        ns = np.random.rand(ntot) * 100  # new color values
        sc.set_array(ns)  # update scatter color data
        ax.set_title(f"Update {i+1}")
        plt.draw()
        plt.pause(0.1)  # wait 5 seconds

    plt.ioff()  # turn off interactive mode when done
    plt.show()


# Setup the tables
# names 
# priority [p1,p2,p3]


# Display the first few rows
# print(df.head())
