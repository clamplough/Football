#CL8/9/17
#import-------------------------------------------------------------------------
from bs4 import BeautifulSoup as bs
import requests
import time
import random

#make assignment for html.parser easily swappable, reduce redundant code
#downloads page content using beautifulsoup with html.parser (lxml is possible replacement for speed)
def parse_page(URL):
    page = requests.get(URL)
    page_content = bs(page.content, 'html.parser')
    return page_content

#main functions-----------------------------------------------------------------
#obtain url information from website for associated ranks pages
def main_url_pull(url):
    #initialize variables
    t0 = time.time()
    t1 = 0
    fails = 0
    URLS = ''
    #attempt to get url information for up to 10 seconds
    while  t1 < 10:
        t1 = time.time() - t0
        try:
            url_ranks_redirect = url + get_ranks_page(url) #url of page opened by going to 'Ranks' (normally QB page)
            URLS = get_rank_urls( url_ranks_redirect ) #list of urls for all pages
            break
        except:
            #try again
            continue
    #if successful call return value
    if URLS:     
        return URLS
    #if unssucssful call make record, add wait delay, and call again
    else:
        fails += 1
        time.sleep(5)
        #if failed 4 times (~1 minute of trying) exit
        if fails > 3:
            return None #this will crash main script, to be restarted later
        main_url_pull(url)

#pull rank information from a list of URLs for each position
#return dictionary of ranks
def main_ranks_pull(positions, URLS):
    ranks = dict()   
    pos_i = 0  
    while pos_i < len(positions):
        position = positions[ pos_i ] #get position
        url = URLS[ position ] #get position url
        page_content = parse_page(url) #get position page
        ranks_date = get_page_date( page_content ) #get position date
        #insert logic here to compare the date to date in database, and 'continue' if not newer
        if position in ['RB', 'WR']:
            position_ranks = get_ranks_ppr(page_content) #filters specific to PPR page setup
        else:
            position_ranks = get_ranks_basic(page_content) #filters for either type of mode
        #insert date and name of analyst for tracking
        position_ranks.insert(0, ranks_date) #add date to data
        position_ranks.insert(0, 'Christopher Harris')
        ranks[ position ] = position_ranks #assign data to dictionary
        fails = 0
        pos_i += 1
    return ranks

#URL Functions------------------------------------------------------------------
#determine the url for ranks page (default position unknown)
#use link to redirect and determine positional ranking links
def get_ranks_page(url_base):
    page_content = parse_page(url_base)
    main_nav = page_content.find('nav', id='main-navigation')
    for heading in main_nav.find_all('a'):
        title = heading.get_text().strip()
        if title == 'Ranks':
            return heading['href']

#get all urls from the base rank page, store them in dictionary for quick access
def get_rank_urls(url_ranks_redirect):
    #determine the base page that 'Ranks' redirects to
    redirect_position, other_positions, main_ranks = find_redirect_position(url_ranks_redirect)
    url_ranks = dict()
    url_ranks[ redirect_position ] = url_ranks_redirect #known position url
    for heading in main_ranks.find_all('a'):
        position = heading.get_text()
        #check other position titles, pull link, add to dictionary
        if position in other_positions:
            url_position = url_base + heading['href']
            url_ranks[ position ] = url_position
    return url_ranks

#determine position of redirected rankings (known that one is sent to a position page)
def find_redirect_position(url_ranks_redirect):
    #first get all the titles of every possible position
    ranks_content = parse_page(url_ranks_redirect)
    #look at main nav, then title block
    main_ranks = ranks_content.find('div', class_='sqs-block-content')
    titles = main_ranks.find('p', class_='text-align-center').get_text()
    #split into list, form set for comparison
    titles = titles.split('|')
    all_titles = set()
    for title in titles:
        all_titles.add( title.strip() )

    #form set of all titles that have a link attached (redirected position has no link)
    link_titles = set()
    for heading in main_ranks.find_all('a'):
        title = heading.get_text().strip()
        link_titles.add(title)
    #compute set difference for page position, then assign to list for indexing (only has 1 item in list)
    redirect_title = all_titles - link_titles
    redirect_title = list(redirect_title)[0]
    return redirect_title, link_titles, main_ranks

#take date from webpage information
def get_page_date(page_content):
    #look at the headings and find the updated line for information date
    headings = page_content.find('div', class_='sqs-block-content')
    for heading in headings.find_all('p'):
        text = heading.get_text()
        if 'updated' in text:
            #trim the text to the specific date
            date = date_extract(text)
            return date

#pull date from text string
def date_extract(s):
    s = s.lstrip('(').rstrip(')')
    parts = s.split(' ')
    return parts[1]

#tag heirarchy <table>--<tr>
def get_ranks_basic(page_content):
    raw_ranks = page_content.find('table')
    rows = raw_ranks.find_all('tr')
    ranks = log_players(rows)
    return ranks

#tag heirarchy <table>--<tr>, but multiple tables to look at
def get_ranks_ppr(page_content):
    raw_ranks = page_content.find_all('table')
    #verify the table heading has the correct scoring type
    for table in raw_ranks:
        scoring_type = table.find('tr').get_text().strip()
        if scoring_type != 'PPR Scoring':
            continue
    rows = table.find_all('tr')[1:] #isolate table rows but eliminate first row (scoring type)
    ranks = log_players(rows)
    return ranks

#read table information and store players in list
def log_players(rows):
    ranks = list()   
    for row in rows:
        cols = row.find_all('td') #break the rows into columns
        #format player
        for col in cols:
            col = col.get_text().strip()
            #if column is rank number
            if col.isdigit():
                num = col
                if len(col) < 2:
                    num = '0' + col
            #elif column is player name
            elif ' ' in col:
                name = col
            #else the column is team acronym
            else:
                team = col
        player = num + '-' + name + '-' + team
        ranks.append(player)
    return ranks

if __name__ == '__main__':
        time.sleep(0) #can replace timing here with 30 seconds to wait if running multiple times within a loop
        
        #obtain rank page urls
        url_base = 'https://www.harrisfootball.com'
        URLS = main_url_pull(url_base)   
            
        #iteration variables
        positions = ['QB', 'RB', 'WR', 'TE', 'DEF']
        
        fails = 0 #failure counter
        while fails < 15:
            try:                  
                ranks = main_ranks_pull(positions, URLS)
                break
            except:
                fails += 1
                continue