from bs4 import BeautifulSoup
import sys
import pandas as pd
import numpy as np

class AttendeeScraper:
    def __init__(self, filepath):
        self.filepath = filepath
        self.soup = None
        self.attendees_guest_map={}
        self.attendees=None


    def load_html(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            html = f.read()
        self.soup = BeautifulSoup(html, 'html.parser')

    def get_attendees(self):
        ''' Scrapes the attendees and their guests from the html
        Each booking_group is in "class_='booking-group'"
        In each one, the attendee has format "font-weight:500"
        and the guests of each one has "text-indent: 10px".
        This has been found from "inspect element" on the html
        '''
        booking_groups = self.soup.find_all('div', class_='booking-group')
        for group in booking_groups:
            attendees = group.find_all("p", style=lambda value: value and "font-weight:500" in value)
            guests_of_atendee = group.find_all("p", style=lambda value: value and "text-indent: 10px" in value)
            if len(attendees)>1:
                print('warning: unexpected formatting')
            for attendee in attendees:
                attendee_name = attendee.get_text(strip=True).replace("(Caian ticket - Drinking)", "")
                ## add the attendee to the dict
                self.attendees_guest_map[attendee_name]=[]
            n=1
            for guest in guests_of_atendee:
                ## add the guests to the dictionary
                guest_name = guest.get_text(strip=True).replace("(Caian ticket - Drinking)", "")
                if guest_name != 'Guest':
                    self.attendees_guest_map[attendee_name].append(guest_name)
                else: # If name not given default "to Guest of ..."
                    self.attendees_guest_map[attendee_name].append(f'Guest of {attendee_name} ({n})')
                    # self.attendees_guest_map[attendee_name].append(f'Guest of {attendee_name}')
                    n+=1
        self.attendees=list(self.attendees_guest_map.keys())
        self.everyone=[]
        for attendee, guests in self.attendees_guest_map.items():
            self.everyone.append(attendee)
            self.everyone.extend(guests)
        self.everyone=np.array(self.everyone)
        self.all_named= [name for name in self.everyone if not name.startswith("Guest of")]

        return

    def pretty_print(self):
        ''' print out the attendees and guests'''
        if self.attendees is None: 
            sys.exit('need to get the data first silly')
        # for attendee in self.attendees:
            # print(attendee)
        for name in self.all_named:
            print(name)
        # sys.exit()
            # for guest in self.attendees_guest_map[attendee]:
                # print(f'__{guest}')

    def find(self,name):
        ''' find the index of the name in the everyone list'''
        index_list=[]
        for indx,person in enumerate(self.everyone):
            if name==person: index_list.append(indx)
        if len(index_list)==0: # noone found
            if not pd.isna(name): # if nan, noone was selected --> if not nan, error in name list
                sys.exit(f'guest not found in everyone list.\n their name is {name}')
            return name
        elif len(index_list)>1:
            sys.exit('duplicates found')
        return index_list[0]



# Replace with your saved file path
# filename = "/mnt/c/Users/Cole/Downloads/Upay - Event Booking.html"

# guestlist=AttendeeScraper(filename)
# guestlist.load_html()
# guestlist.get_attendees()
# guestlist.pretty_print()

