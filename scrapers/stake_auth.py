import requests
import json
import os

class AuthClass:
    API_URL = "https://api.stake.com/graphql"
    
    @staticmethod
    def get_headers():
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'https://stake.com',
            'Referer': 'https://stake.com/sports/esports',
            'X-API-Key': os.getenv('STAKE_API_KEY', ''),
            'X-Device-UUID': os.getenv('STAKE_DEVICE_UUID', ''),
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        } 
