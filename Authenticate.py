import json, requests
from datetime import datetime

class Authenticate():
    def __init__(self):
        self.config = json.load(open('config.json'))
        self.today = datetime.today()

    def books_refresh_token(self):
        # update the token value and token_datetime in config.json and save the file
        headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
        params = {
            'refresh_token': self.config['books_refresh_token'], 
            'client_id': self.config['client_id'], 
            'client_secret': self.config['client_secret'],
            'redirect_uri': self.config['books_redirect_uri'], 
            'grant_type': 'refresh_token'
        }
        r = requests.post('https://accounts.zoho.com/oauth/v2/token', params=params, headers=headers)
        token = r.json()['access_token']
        self.config['books_access_token'] = token
        self.config['token_datetime'] = str(self.today)
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        print(token)
        return
    
    def check_date(self):
        # confirm that today() is within 1 hour of self.config['token_datetime']
        token_date = datetime.strptime(self.config['token_datetime'], '%Y-%m-%d %H:%M:%S.%f')
        difference = self.today - token_date
        seconds_in_day = 24 * 60 * 60
        minutes, seconds = divmod(difference.days * seconds_in_day + difference.seconds, 60)
        if minutes >= 60:
            print(f"Zoho token is expired by {minutes-60} minutes.")
            self.books_refresh_token()
        else:
            print(f"Zoho token is still valid for {60-minutes} minutes.")
        return
