import numpy as np
import sys

''' All of the functions to measure happiness etc'''

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

def ij_andnearby(person_i,person_j,A,P,G,s,p):
    """Happiness of person_i, person_j, and all their adjacent neighbors (no double counting)."""
    seat_i, seat_j = s[person_i], s[person_j]
    adj_i, adj_j = A.getrow(seat_i), A.getrow(seat_j)
    # All affected seats (combine neighbors)
    combined_indices = np.unique(np.concatenate([adj_i.indices, adj_j.indices]))
    # Map seats to people sitting there
    affected_people = np.unique(np.concatenate([[person_i, person_j], p[combined_indices]]))
    
    # Sum happiness for all affected people
    total = sum(happiness(person, A, P, G, s) for person in affected_people)
    return total

def trial_move(ntot,s,p,A,P,G,h):
    i, j = np.random.choice(ntot, size=2, replace=False)
    s_trial, p_trial = swap_seats(i, j, s.copy(), p.copy())
    h_trial = total_happiness(A, P, G, p_trial, s_trial)
    return h_trial - h,h_trial,s_trial,p_trial

def trial_move2(ntot,s,p,A,P,G):
    i, j = np.random.choice(ntot, size=2, replace=False)
    h0 =ij_andnearby(i,j,A,P,G,s,p)
    s_trial, p_trial = swap_seats(i, j, s.copy(), p.copy())
    h1 =ij_andnearby(i,j,A,P,G,s_trial,p_trial) 

    return h1-h0,s_trial,p_trial


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

def sat_with_friends(s,A,P,attendee,guestlist):
    ''' Check that the selected person is sat with all of their friends (high priorities)'''
    person_i=guestlist.find(attendee)
    person_seat = s[person_i]
    adjacents = A.getrow(person_seat)    # adjacency for this person's seat

    count=0
    total=0
    pissed=[]
    friends = P.getrow(person_i)      # preferences for other people (value is how much, index is the friend index)
    for friend_pref, friend_seat in zip(friends.data, s[friends.indices]):
        if friend_pref<=3: continue #skip those who dont really care
        total+=1
        for adj_seat in adjacents.indices:
            if friend_seat == adj_seat:
                count+=1
                break
    if (count==0) and (len(friends.indices)!=0):  
        pissed=[person_i]
    return count, total, pissed


def sat_with_guests(s,A,attendee,guestlist):
    ''' Check that the selected person is sat with all of their guests'''
    person_i=guestlist.find(attendee)
    seat_number = s[person_i]
    name=guestlist.everyone[person_i]

    adjacents = A.getrow(seat_number)    # adjacency for this person's seat
    count=0
    total=0
    for guest in guestlist.attendees_guest_map[name]:
        total+=1
        guest_indx=guestlist.find(guest)
        guest_location=s[guest_indx]
        for adj_indx in adjacents.indices:
            if guest_location == adj_indx:
                count+=1
                break
    return count, total

def all_sat_with_guests(s,A,guestlist):
    score=0;total=0
    for attendee in guestlist.attendees: 
        si, ti = sat_with_guests(s,A,attendee,guestlist)
        score+=si ; total+= ti
    return score,total

def all_sat_with_friends(s,A,P,guestlist):
    score=0;total=0;pissed=[]
    for attendee in guestlist.attendees: 
        si, ti, pi = sat_with_friends(s,A,P,attendee,guestlist)
        score+=si ; total+= ti; pissed.extend(pi)
    outstr=f'SCORE2: {score} of {total}. People pissed:\n'
    for pi in pissed:
        outstr+= f'___ {guestlist.everyone[pi]}\n'
    return outstr

