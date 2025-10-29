import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy.linalg import block_diag
from matplotlib.widgets import Button
from setup import get_Matrices,plot_setup
from scipy.sparse import csr_matrix

### Get the names from Upay and seating form responses to generate the Matrices required
event_booking_html = "/mnt/c/Users/Cole/Downloads/Upay - Event Booking.html"
seating_form_responses = "/mnt/c/Users/Cole/Downloads/Superhall Seating Request Form (Responses).xlsx"
A,P,G,seat_positions = get_Matrices(event_booking_html,seating_form_responses) #matrices in csr format
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

def happiness(person_indx,A,P,G,s):
    """    
    1. find the persons seat number
    2. find the person index of the persons preferences
    3. find the places next to the person
    4. go through and compare the  
    """
    h = 0.0
    seat_number = s[person_indx]

    friends = P.getrow(person_indx)      # preferences for other people
    adjacents = A.getrow(seat_number)    # adjacency for this person's seat

    # Iterate through friends and adjacent seats
    for friend_pref, friend_seat in zip(friends.data, s[friends.indices]):
        for adj_weight, adj_seat in zip(adjacents.data, adjacents.indices):
            if friend_seat == adj_seat:
                h += friend_pref * adj_weight
    # Add the Gallery contribution
    h += G[person_indx,seat_number]

    return h

def all_happiness(A,P,G,p,s):
    return np.array([happiness(p_indx,A,P,G,s) for p_indx in p])

def total_happiness(A,P,G,p,s):
    return np.sum(all_happiness(A,P,G,p,s))

def swap_seats(person_i,person_j,s,p):
    ''' Swap person index i and person index j in both the maps'''
    # Update the seat of person_i and person_j
    s[person_i],s[person_j]=s[person_j],s[person_i]
    # Update the invesr map accordingly
    p[s[person_i]],p[s[person_j]]=person_i,person_j
    return s,p


### Initial conditions
s0=np.arange(ntot)
p0=np.arange(ntot)
h0=total_happiness(A,P,G,p0,s0)
### Setup the plot
sc,ax,stop_button,text_labels=plot_setup(plt,seat_positions,all_happiness(A,P,G,p0,s0),p0)
def stop(event):sys.exit()
stop_button.on_clicked(stop)
T=1
for it in range(1000):  

    i, j = np.random.choice(ntot, size=2, replace=False)
    s,p=swap_seats(i,j,s0.copy(),p0.copy())
    h=total_happiness(A,P,G,p,s)

    delta_h = h - h0
    print(h)

    # Always accept if better, otherwise accept with probability exp(delta_h / T)
    if delta_h > 0 or np.random.rand() < np.exp(delta_h / T):
        h0=h
        s0=s.copy()
        p0=p.copy()
        sc.set_array(all_happiness(A,P,G,p,s))                   # update scatter color data
        for person_idx, t in enumerate(text_labels): #update 
            t.set_text(p[person_idx])  # 


    ax.set_title(f"Update {it+1}")

    plt.draw()
    plt.pause(0.00001)  # wait 5 seconds

plt.ioff()  # turn off interactive mode when done
plt.show()


