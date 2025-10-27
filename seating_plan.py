import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy.linalg import block_diag
from matplotlib.widgets import Button
from setup import get_Matrices,plot_setup

### Get the names from Upay and seating form responses to generate the Matrices required
event_booking_html = "/mnt/c/Users/Cole/Downloads/Upay - Event Booking.html"
seating_form_responses = "/mnt/c/Users/Cole/Downloads/Superhall Seating Request Form (Responses).xlsx"
A,P,T,G,seat_positions = get_Matrices(event_booking_html,seating_form_responses)
ntot=T.shape[0]

### Setup the plot
# happiness=np.zeros((ntot))
happiness = np.random.rand(ntot) * 100  # new color values

sc,ax,stop_button=plot_setup(plt,seat_positions,happiness)
def stop(event):sys.exit()
stop_button.on_clicked(stop)
'''
Calculate the seating plan using Monte Carlo.
A: adjacency matrix [seats->seats]         Gives score of how good seating is. e.g. A12 = how good is it for 1 to sit with 2
P: preference matrix [people->people]      Gives people's preference of sitting next to eachother. e.g. P23 = how person 2 rated 3
T: transformation matrix [people->seats]   Stores the position of each person (binary choice)
G: gallery matrix [people->seats]          Stores preferences of people to be in gallery. Also if needed can add biasing for seats to be at end of table
'''

# Loop that updates colors every 5 seconds
for i in range(1000):  # update 10 times

    ns = np.random.rand(ntot) * 100  # new color values
    sc.set_array(ns)  # update scatter color data
    ax.set_title(f"Update {i+1}")
    plt.draw()
    plt.pause(0.001)  # wait 5 seconds

plt.ioff()  # turn off interactive mode when done
plt.show()


# Setup the tables
# names 
# priority [p1,p2,p3]


# Display the first few rows
# print(df.head())
