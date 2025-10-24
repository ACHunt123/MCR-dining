import pandas as pd
import numpy as np
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
A=np.zeros((nsts,nsts))
def A_longtable(nsts):
    assert nsts%2==0,'number of seats on table must be even'
    A_block=np.zeros((nsts,nsts))
    l_indices=np.arange(0,nsts//2)
    r_indices=np.arange(nsts//2,nsts)
    for l_indx,r_indx in zip(l_indices,r_indices):
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
    return A_block

def A_squaretable(nsts):
    assert (nsts-4)%4==0,'number of seats on table must be 4n-4'
    A_block=np.zeros((nsts,nsts))
    indices=np.arange(0,nsts)
    for indx in indices:
        ### weights
        w_adjacent1=3
        w_adjacent2=1

        # directly next to eachother 
        if indx+1 in indices:
            A_block[indx,indx+1]=A_block[indx+1,indx]=w_adjacent1
        else:
            A_block[indx,0]=A_block[0,indx]=w_adjacent1 #last one
        # two away
        if indx+2 in indices:
            A_block[indx,indx+2]=A_block[indx+2,indx]=w_adjacent2
        else:
            A_block[indx,0]=A_block[0,indx]=w_adjacent2 #last one
    print(A_block)
    return A_block

A_longtable(10)
A_squaretable(8)


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
    gallery_seat_indices = [2, 4, 7, 9]
    if gallery_pref=='Yes':
        G[name_indx,gallery_seat_indices]=gallery_weight


    

# Setup the tables
# names 
# priority [p1,p2,p3]


# Display the first few rows
# print(df.head())
