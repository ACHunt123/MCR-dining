import sys
sys.path.append("/home/ach221/software/MCR-Dining")
from getnames import AttendeeScraper



folder='/mnt/c/Users/Cole/Downloads'
folder='/home/colehunt/software/MCR-dining/data'
folder='/home/ach221/Downloads'
### Get the names from Upay and seating form responses to generate the Matrices required
event_booking_html = f"{folder}/Upay - Event Booking.html"
seating_form_responses = f"{folder}/Superhall Seating Request Form (Responses).xlsx"
swaps_xls = f"{folder}/MTSuperhallSwaps2025-26.xlsx"

### Get the names from Upay
guestlist=AttendeeScraper(event_booking_html,swaps_xls)
guestlist.load_Upay()
guestlist.load_Swaps()
guestlist.pretty_print()