import numpy as np

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

def sat_with_guests(s,A,attendee,guestlist):
    ''' Check that the selected person is sat with all of their guests'''
    person_i=guestlist.find(attendee)
    seat_number = s[person_i]
    name=guestlist.everyone[person_i]

    adjacents = A.getrow(seat_number)    # adjacency for this person's seat

    #   attendee_indx=guestlist.find(attendee)
    count=0
    total=0
    for guest in guestlist.attendees_guest_map[name]:
        total+=1
        guest_indx=guestlist.find(guest)
        guest_location=s[guest_indx]
        for adj_indx in adjacents.indices:
            if guest_location == adj_indx:
                count+=1
    return count, total

def all_sat_with_guests(s,A,guestlist):
    score=0;total=0
    for attendee in guestlist.attendees: 
        si, ti = sat_with_guests(s,A,attendee,guestlist)
        score+=si ; total+= ti
    print(f'SCORE: {score} of {total}')