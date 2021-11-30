import argparse
import http.client
import json
import pprint
import time
from datetime import date, datetime, timedelta

pp = pprint.PrettyPrinter(indent=2, width=80, sort_dicts=True, compact=False)

DateFormat = "%Y-%m-%d"
PDL_ID = '25212011521042'
conn = http.client.HTTPSConnection("enedisgateway.tech")
types = [
    "consumption_load_curve",
    "daily_consumption_max_power",
    "daily_consumption", 
    "production_load_curve", 
    "daily_production", 
    "identity", 
    "contracts", 
    "addresses"
]
payload = {
    'type':           '<TYPE>',
    'usage_point_id': '<PDL_ID>',
    'start':          '<START_DATE>',
    'end':            '<END_DATE>',
    # 'quality': 'B',
    # 'interval-reading': 
}

headers = {
    'Authorization': "<AUTH>",
    'Content-Type': "application/json",
}

def run(args):
    headers['Authorization'] = args.auth
    payload['usage_point_id'] = args.pdlid
    payload['start'] = args.start_date.strftime(DateFormat)
    payload['end'] = args.end_date.strftime(DateFormat)
    
    for type in types:
        payload['type'] = type
        print(f'Acquisition de {type}')
        pp.pprint(payload)
        conn.request("POST", "/api", json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        data = json.loads(data.decode("utf-8"))
        pp.pprint(data)

        time.sleep(1)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''
################
Enedis collector
################
''')
    parser.add_argument('--auth', '-a', metavar='<AUTH>', type=str,
                        help='Authorization token, like mogHR8VzTLwrn...JFxlM '
                             'Get it on: https://enedisgateway.tech',
                        required=True)
    parser.add_argument('--pdlid', '-p', metavar='<PDL_ID>', type=str,
                        help='PDL identifier, like 12345678901234 '
                        'Get it on: '
                        'https://mon-compte-particulier.enedis.fr/compteur/',
                        required=True)
    parser.add_argument('--start-date', '-s',
                        metavar='<START_DATE YYYY-MM-DD>',
                        type=date.fromisoformat, default=None,
                        help='Start date (Default start date - 7 days)')
    parser.add_argument('--end-date', '-e',
                        metavar='<END_DATE YYY-MM-DD>',
                        type=date.fromisoformat,
                        default=datetime.now()-timedelta(days=1),
                        help='End date (Default yesterday)')

    args = parser.parse_args()
    if args.start_date is None:
        args.start_date = args.end_date - timedelta(days=7)

    run(args)