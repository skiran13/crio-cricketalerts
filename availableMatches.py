import requests
from bs4 import BeautifulSoup as bs


matchLinks = []
matchTitles =[]

# Function to show the currently available live matches
def show_current():
    page = requests.get('https://www.cricbuzz.com/cricket-match/live-scores').text

    # Initialize html parser
    soup = bs(page, 'html.parser')

    # Variable to store all the <h3> tags
    h3s= soup.find_all('h3')

    # Variable to store all the <a> tags
    a_s = []
    for i in range(len(h3s)):
        a_s.append(h3s[i].find_all('a'))

    global matchLinks
    global matchTitles
    matchLinks=[]
    matchTitles=[]

    # Append all the match titles and links to the global array
    for i in range(len(a_s)):
        matchTitles.append(a_s[i][0]['title'])
        matchLinks.append(a_s[i][0]['href'])

    i=0
    msg=''
    for title, link in zip(matchTitles, matchLinks):
        i+=1
        msg=f'{msg}\n{i}. {title}'
    return msg