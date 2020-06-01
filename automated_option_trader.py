import pandas as pd
import tkinter as tk
import datetime 
import holidays
import requests
import json

import robin_stocks as r
import robin_stocks.helper as helper

import praw
reddit = praw.Reddit(client_id='xxxxx',
                     client_secret='xxxxx',
                     user_agent='xxxxx',
                     password='xxxxx',
                     username='xxxxx')

username = 'xxxxx'
password = 'xxxxx'
login = r.login(username, password, store_session=True)
account=r.build_user_profile()

def get_cutoff (max_option_price):
# Get Stock List

    cash = float(account['cash']) 
    half_cash = 0.5*cash
    budget = min(cash, max_option_price)
    
    max_stock_price = max_option_price/2
    cutoff = min(half_cash, max_stock_price)
    
    print('Current buying power: ${0:.2f}'.format(cash))
    print('Maximum option price: ${0:.2f}'.format(budget,2))
    print('Ticker price cutoff: ${0:.2f}'.format(cutoff,2))
    return cutoff, budget 

def get_affordable_stocks (cutoff):
# Takes cutoff price and return S&P stocks valued at less

    #sp_table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    #sp_list = sp_table[0]['Symbol'].tolist()    
    
    sp_list = ['AMD', 'AES', 'AFL', 'ALK', 'ADS', 'LNT', 'MO', 'AMCR', 'AAL', 'AIG', 'T', 'AOS', 'APA', 'AIV', 'AMAT', 'APTV', 'ADM', 'ARNC', 'BKR', 'BAC', 'BK', 'BWA', 'BSX', 'BMY', 'BF.B', 'COG', 'CPB', 'COF', 'CPRI', 'CAH', 'KMX', 'CCL', 'CBRE', 'CNC', 'CNP', 'CTL', 'CF', 'SCHW', 'CSCO', 'C', 'CFG', 'CMS', 'KO', 'CTSH', 'CMCSA', 'CMA', 'CAG', 'CXO', 'COP', 'GLW', 'CTVA', 'COTY', 'CSX', 'DHI', 'DRI', 'DAL', 'XRAY', 'DVN', 'FANG', 'DFS', 'DISCA', 'DISCK', 'DISH', 'DOW', 'DRE', 'DD', 'DXC', 'ETFC', 'EMN', 'EBAY', 'EIX', 'EMR', 'EOG', 'EVRG', 'EXC', 'EXPE', 'XOM', 'FAST', 'FITB', 'FE', 'FLIR', 'FLS', 'F', 'FTV', 'FBHS', 'FOXA', 'FOX', 'BEN', 'FCX', 'GPS', 'GE', 'GM', 'HRB', 'HAL', 'HBI', 'HOG', 'HIG', 'HAS', 'PEAK', 'HP', 'HSIC', 'HES', 'HPE', 'HFC', 'HOLX', 'HRL', 'HST', 'HPQ', 'HBAN', 'INFO', 'IR', 'INTC', 'IP', 'IPG', 'IVZ', 'IRM', 'JCI', 'JNPR', 'KEY', 'KIM', 'KMI', 'KSS', 'KHC', 'KR', 'LB', 'LW', 'LVS', 'LEG', 'LEN', 'LNC', 'LYV', 'LKQ', 'L', 'LYB', 'M', 'MRO', 'MPC', 'MAS', 'MXIM', 'MET', 'MGM', 'MU', 'TAP', 'MDLZ', 'MS', 'MOS', 'MYL', 'NOV', 'NTAP', 'NWL', 'NEM', 'NWSA', 'NWS', 'NLSN', 'NI', 'NBL', 'JWN', 'NLOK', 'NCLH', 'NRG', 'NUE', 'OXY', 'OMC', 'OKE', 'ORCL', 'PNR', 'PBCT', 'PRGO', 'PFE', 'PSX', 'PPL', 'PFG', 'PRU', 'PEG', 'PHM', 'PVH', 'PWR', 'O', 'REG', 'RF', 'RHI', 'ROL', 'RCL', 'SLB', 'STX', 'SEE', 'SPG', 'SLG', 'SO', 'LUV', 'STT', 'SYF', 'SYY', 'TPR', 'FTI', 'TXT', 'TJX', 'TFC', 'TWTR', 'UDR', 'USB', 'UAA', 'UA', 'UAL', 'UNM', 'VLO', 'VTR', 'VIAC', 'VNO', 'WRB', 'WAB', 'WBA', 'WFC', 'WELL', 'WDC', 'WU', 'WRK', 'WY', 'WMB', 'XEL', 'XRX', 'ZION']
    
    affordable_tickers=[]
    price=0
    
    print('Number of stocks to check:', len(sp_list))
    for ticker in sp_list:
        price = get_stock_price(ticker)
        if price < cutoff:
            affordable_tickers.append(ticker)
            
    print('Number of stocks under ${} cutoff: {}'.format(cutoff,len(affordable_tickers)))
            
    return affordable_tickers

def get_new_mentions(subreddit,stock_list):
# Gets the counts of mentions/calls/puts from past 2 days

    print ('Start of reddit search:',datetime.datetime.today().strftime("%H:%M"))

    print('Getting yesterdays words')
    yesterday_words = get_words_for_date('wallstreetbets', 0)
    
    print('Getting day befores words')
    day_before_words = get_words_for_date('wallstreetbets', 1)
    
    yesterday_counts  = ticker_counts(yesterday_words, stock_list)
    day_before_counts = ticker_counts(day_before_words, stock_list)
    
    cols = ['Total Past 24','Calls Past 24','Puts Past 24','Total Day Before','Calls Day Before','Puts Day Before']
    
    new_mentions = yesterday_counts.merge(day_before_counts,right_index=True,left_index=True);
    new_mentions.columns = cols
    
    total_scores  = []
    call_scores   = []
    put_scores    = []
    larger_scores = []
    for ticker in new_mentions.index:
    
        total_past_day   = new_mentions.at[ticker, 'Total Past 24'   ]
        total_day_before = new_mentions.at[ticker, 'Total Day Before']
        
        calls_past_day   = new_mentions.at[ticker, 'Calls Past 24'   ]
        calls_day_before = new_mentions.at[ticker, 'Calls Day Before']
        
        puts_past_day   = new_mentions.at[ticker, 'Puts Past 24'   ]
        puts_day_before = new_mentions.at[ticker, 'Puts Day Before']
    
        total_score  = total_past_day - total_day_before #new mentions
        calls_score  = calls_past_day - calls_day_before #new calls
        puts_score   = puts_past_day  - puts_day_before  #new puts
        larger_score = max([calls_score, puts_score])    #max of new call/new puts
        
        total_scores.append(total_score)
        call_scores.append(calls_score)
        put_scores.append(puts_score)
        larger_scores.append(larger_score)
        
    new_mentions['New Mentions'       ] = total_scores
    new_mentions['New Calls'          ] = call_scores
    new_mentions['New Puts'           ] = put_scores
    new_mentions['Larger New Call/Put'] = larger_scores #can sort to find stock with most new hype
    
    new_mentions.sort_values(by=['New Mentions'],ascending = False, inplace=True)
    
    print ('end:',datetime.datetime.today().strftime("%H:%M"))
    
    return new_mentions

def ticker_counts(words_string, ticker_list):
# Counts the number of mentions/calls/puts
  
    dicts = {}
    keys = ticker_list
    all_words = words_string
    search_range = 30
    
    for i in keys:
        count = 0
        call_count = 0
        put_count = 0 
        indices = []
        
        if i == 'DD':
            i='DuPont'
        if i == 'A':
            i='Agilent'
        
        search_terms = [" " + i + " ", " " + i + ".", " " + i + ",", " " + i + "!", " " + i + "?", "(" + i + ")",
                        "$" + i + " ", "$" + i + ".", "$" + i + ",", "$" + i + "!", "$" + i + "?", "($" + i + ")"]
        
        for term in search_terms:
            count+= all_words.count(term)
            indices += find_all(all_words, term)
        for index in indices:
            context = all_words[index-search_range:index+search_range]
            call_count += context.count('call')
            call_count += context.count('Call')
            put_count += context.count('put')
            put_count += context.count('Put')
            
        if i == 'DuPont':
            i='DD'
        if i == 'Agilent':
            i='A'
        dicts[i] = [count,call_count,put_count]
        
    df = pd.DataFrame.from_dict(dicts,orient='index',columns=["total counts", "call counts", "put counts"])
    df.sort_values(by=["total counts"],ascending = False, inplace=True)
    
    return df

def get_data(after, before, post_type ,sub):
    """gets on page of data from pushshift.io"""
    
    url = 'https://api.pushshift.io/reddit/{}/search/?subreddit={}&size=1000&after={}&before={}'.format(post_type,sub,after,before)
    data_found = False
    while data_found == False:
        try:
            r = requests.get(url)
            data = json.loads(r.text)
        except Exception:
            pass
        else:
            data_found = True
            
    return data['data']

def get_words_for_date(sub, days_ago):
    """Returns a DataFrame of submission info"""
    
    end_time = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    start_time = end_time - datetime.timedelta(days=1)
    before = int(end_time.timestamp())
    after = int(start_time.timestamp())


    submissions = get_data(after, before, 'submission', sub)
    comments = get_data(after, before, 'comment', sub)


    words = ''

    print('Getting submissions')
    while len(submissions) > 0:
        for submission in submissions:
            try:
                title = submission['title']
                selftext = submission['selftext']
            except Exception:
                words += title + ' '
            else:
                words += title + ' ' + selftext + ' '
        after = submissions[-1]['created_utc']
        submissions = get_data(after, before, 'submission', sub)

    print('Getting comments')
    while len(comments) > 0:
        for comment in comments:
            try:
                body = comment['body']
            except Exception:
                pass
            else:
                words += body + ' '
        after = comments[-1]['created_utc']
        current_datetime = datetime.datetime.fromtimestamp(after)
        print("Getting comment data at:", datetime.datetime.strftime(current_datetime,"%Y-%m-%d %H:%M"))
        comments = get_data(after, before, 'comment', sub)

    return words  

def words_in_submissions(sub_ids):
# Gets all the words from a list of submission ids 
    
    all_words=''

    for submission in sub_ids:
        all_words += submission.title
        all_words += ' '
        all_words += submission.selftext
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            all_words+=comment.body
            all_words+=' '
            
    return all_words

def submissions_within_24_hours(subreddit,days_ago): #0 days_ago gives past 24 hours. Only goes back to 6 day_ago...odd
# Gets the submission ids of all posts in last 24 hrs 
    subreddit = reddit.subreddit(subreddit)

    submissionsIn24 = [] #list
    for submission in subreddit.new(limit=10000): #There are bigger problems if over 10,000 submissions are posted
        submissionDate = datetime.datetime.utcfromtimestamp(submission.created)+datetime.timedelta(hours=-8)
        currentTime = datetime.datetime.utcnow()+datetime.timedelta(days=-days_ago)
        difference = currentTime - submissionDate

        if 'day' not in str(difference):
            submissionsIn24.append(submission)

    return submissionsIn24

def find_all(a_str, sub):
# Finds the starting index of a substring in a string 
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches

def find_stock_and_type_and_exp_date (stocks_info,budget):
# Choose the option ticker, type, and expiration to buy 

    today = datetime.datetime.today()
    
    #1)Sort the stock info to user's liking

    if stocks_info['Calls Past 24'].sum() > stocks_info['Puts Past 24'].sum():
        stocks_info.sort_values(by=['New Calls'],ascending = False, inplace=True)
        #opt_type = 'call'
        opt_type = 'put' #fading the trend
    else:
        stocks_info.sort_values(by=['New Puts'],ascending = False, inplace=True)
        #opt_type = 'put'
        opt_type = 'call' #fading the trend

    print('The stocks have been sorted. Top 3 choices:', stocks_info.index[0], stocks_info.index[1], stocks_info.index[2])
        
    #2) Iterate though the list to find an option that is affordable
    
    affordable = False
    while affordable == False:
        ticker = stocks_info.index[0]
        exp_date = get_expiration(ticker, opt_type)
        print('Looking for a {} {} expiring on {} under ${}.'.format(ticker,opt_type,exp_date,budget))

        affordable = is_affordable (ticker, exp_date, opt_type, budget)

        if affordable:
            print('A {} {} expiring on {} is affordable.'.format(ticker,opt_type,exp_date))
            return ticker, opt_type, exp_date
        else:
            print('The cheapest {} {} expiring on {} is over the budget of ${}.'.format(ticker,opt_type,exp_date,budget))
            stocks_info = stocks_info.drop(ticker)

def is_affordable (symbol, exp_date, opt_type, budget):
        
    try:
        available_options = r.find_options_for_stock_by_expiration(symbol, exp_date, opt_type, info=None)
    except Exception:
        print('\nAPI is unable to get data for {}.\n'.format(symbol))
        return False
        
    print('length of available options:', len(available_options))
    strikes={}
    for opt in available_options:

        price = float(opt['mark_price'])
        strike = float(opt['strike_price'])
        strikes[strike] = price
        
    min_price = min(strikes.values())*100
    
    if budget > min_price:
        return True
    else:
        return False

def get_expiration(symbol,opt_type):
# Takes stock and returns expiration date to buy

    dict = {0: 18, 1: 17, 2: 16, 3: 15, 4: 14, 5: 13, 6: 12}
    today = datetime.datetime.today()
    day = today.weekday() # 0 - 6 for monday - sunday
    addition = dict[day] # number of days to add
    
    exp_date = today + datetime.timedelta(days=addition)
    formatted_exp_date = exp_date.strftime("%Y-%m-%d")
    
    strike = int(get_stock_price(symbol)) #placeholder for testing dates
    if strike > 75: #stocks with high prices don't have options at all integers
        strike = round(strike,-1)
    
    opt_price = get_option_price(symbol, formatted_exp_date, strike, opt_type, 'mark_price');

    
    if type(opt_price) == float:
        return formatted_exp_date
    
    else:
        while type(opt_price) != float:
            exp_date += datetime.timedelta(days=7) #try the next friday
            formatted_exp_date = exp_date.strftime("%Y-%m-%d")
            opt_price = get_option_price(symbol, formatted_exp_date, strike, opt_type, 'mark_price');
        
    return formatted_exp_date
 
def get_strike(ticker,opt_type,exp_date,budget):
# Chooses strike as close to, but not over, budget
    
    available_options = r.find_options_for_stock_by_expiration(ticker, exp_date, opt_type, info=None)
    strikes=[]
    marks=[]
    for opt in available_options:

        marks.append(float(opt['mark_price']))
        strikes.append(float(opt['strike_price']))

    strike_series = pd.Series(strikes) 
    mark_series = pd.Series(marks) 

    price_data =pd.concat([strike_series, mark_series], axis=1)
    price_data.columns = ['Strike Price', 'Mark Price']
    price_data.sort_values(by = 'Mark Price', ascending = True, inplace = True)
    
    counter = 0
    option_value = price_data.iloc[counter,1]*100
    
    while option_value < budget:
        counter +=1
        option_value = price_data.iloc[counter,1]*100
        
    counter -= 1 #counter will go one too far
    
    strike = price_data.iloc[counter,0]
    price = price_data.iloc[counter,1]*100
    return strike, price

def get_option_price (symbol, exp_date, strike, opt_type, info_type):
# Helpful tools to navigate robin_stocks api

    price = r.get_option_market_data(symbol, exp_date, strike, optionType = opt_type, info=info_type)
    
    if type(price) == str:
        return 100*float(price)
    else: 
        return "Not Valid"
    

def get_stock_price (ticker):
    return float(r.get_latest_price(ticker)[0])

def display_message(string):
    
    import tkinter as tk

    root= tk.Tk()
 
    canvas1 = tk.Canvas(root, width = 400, height = 150)
    canvas1.pack()

    label1 = tk.Label(root, text=string)
    canvas1.create_window(200, 75, window=label1)

    root.mainloop()


def after_hours():

    now = datetime.datetime.now()
    openTime = datetime.time(hour = 8, minute = 30, second = 0)
    closeTime = datetime.time(hour = 15, minute = 0, second = 0)
    
    # If a holiday
    us_holidays = holidays.US()
    if now.strftime('%Y-%m-%d') in us_holidays:
        return True
        # If before 0930 or after 1600
    if (now.time() < openTime) or (now.time() > closeTime):
        return True
        # If it's a weekend
    if now.date().weekday() > 4:
        return True

    return False

def get_open_urls():

    positions = r.get_open_option_positions()

    urls = []
    for position in positions:
        urls.append(position['url'])
        
    return urls

def get_open_positions():
    
    positions = r.get_aggregate_positions()
    urls = get_open_urls()
    open_positions = []
    changes = []
    
    for position in positions:

        legs = position['legs'][0]
        url = legs['position']

        if url in urls:

            buy_price = float(position['average_open_price'])
            symbol = position['symbol']
            legs = position['legs'][0]
    
            exp_date = legs['expiration_date']
            strike = legs['strike_price']
            opt_type = legs['option_type']
    
            current_price = get_option_price(symbol, exp_date, strike, opt_type, 'mark_price')
            percent_change = ((current_price-buy_price)/buy_price)*100
            
            position['exp_date'] = exp_date
            position['strike'] = strike
            position['opt_type'] = opt_type
            position['buy_price'] = buy_price
            position['current_price'] = current_price
            position['percent_change'] = percent_change

            open_positions.append(position)

        else:
            pass
    
    return open_positions

def sell_stock():
    choices = get_open_positions()
    changes =[]
    pos_changes = []

    for choice in choices:
        #only sells if over $5
        if choice['current_price'] > 5:
            changes.append(choice['percent_change'])
            if choice['percent_change'] > 0:
                pos_changes.append(choice['percent_change'])
                
    if len(pos_changes) == 1:
        biggest_gain = max(changes)
        for choice in choices:
            if choice['percent_change'] == biggest_gain:

                price = choice['current_price']/100
                price = round(price * 20) / 20
                symbol = choice['symbol']
                exp_date = choice['exp_date']
                strike = choice['strike']
                opt_type = choice['opt_type']

                report = r.order_sell_option_limit('close', 'credit', price = price, symbol = symbol, quantity = 1, expirationDate = exp_date, strike = strike, optionType = opt_type, timeInForce='gfd')
                print(report)
            else:
                pass
    else:
        price = 0
     
    return price*100


if after_hours():
    print ("The stock market is not open now.")
    display_message("The stock market is not open now.")
else:

    money_in = sell_stock()

    cutoff, budget = get_cutoff(50) #max price to pay for single option         
    ticker_list = get_affordable_stocks(cutoff)                                         
    stock_info  = get_new_mentions("wallstreetbets",ticker_list) 
            
    ticker, opt_type, exp_date = find_stock_and_type_and_exp_date(stock_info,budget)
    print('ticker:', ticker)
    print('option type:', opt_type)
    print('expiration date:', exp_date)

    strike, price = get_strike(ticker,opt_type,exp_date,budget)
    print('strike_price: ${0:.2f}'.format(strike))
    print('mark_price: ${0:.2f}'.format(price))


    price    = float(price)
    price    = round(price * 20) / 20
    print ('option price):', price)

    price    = round(price / 100,2)
    print ('option price (per share):', price)

    report = r.order_buy_option_limit('open', 'debit', price = price, symbol = ticker, quantity = 1, expirationDate = exp_date, strike = strike , optionType=opt_type, timeInForce='gfd')
    for entry in report:
        print("{}: {}".format(entry, report[entry]))
        
    try:
        float(report['price']) == price
    except Exception:
        print ('Something has gone wrong')
        display_message('Something has gone wrong.')
        try:
            print(report['detail'])
        except Exception:
            print('Can not find error report')
    else:
        print('A ${} {} {} option expiring on {} was ordered for ${}'.format(strike,ticker, opt_type, exp_date,price))
        display_message('A ${} {} {} option expiring on {} was ordered for ${}'.format(strike,ticker, opt_type, exp_date,price))

        #Add Purchase to Option Log
        new_entry = {}
        new_entry ['Date'] = datetime.datetime.strftime(datetime.datetime.today(), "%Y-%m-%d")
        new_entry ['Transaction'] = 'Buy'
        new_entry ['Symbol'] = ticker
        new_entry ['Option Type'] = opt_type
        new_entry ['Strike Price'] = strike
        new_entry ['Expiration Date'] = exp_date
        new_entry ['Value'] = -1*float(price*100)

        option_log = pd.read_csv(r'C:\Users\GR\Desktop\option_log.csv')
        option_log = option_log.append(new_entry, ignore_index = True)
        option_log.to_csv(r'option_log.csv', index = False)
        print('Option Log has been updated.')
