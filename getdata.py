import argparse
import http.client
import json
import pprint
import time
from datetime import date, datetime, timedelta

class Unbuffered(object):
    def __init__(self, stream):
       self.stream = stream
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        pass
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

DateFormat = "%Y-%m-%d"
conn = http.client.HTTPSConnection("enedisgateway.tech")

types = [
    "addresses",
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
    start = args.start_date
    end = args.end_date
    intervals = []
    if start > end:
        _ = end
        end = start
        start = _
    nIntervals, reminder = divmod((end-start).days, 7)
    currentStart = start
    for _ in range(nIntervals):
        currentEnd = currentStart+timedelta(days=7)
        intervals.append((currentStart.strftime('%Y-%m-%d'),
                          currentEnd.strftime('%Y-%m-%d')))
        currentStart += timedelta(days=7)
    if reminder:
        intervals.append(
            (currentStart.strftime('%Y-%m-%d'),
            (currentStart+timedelta(days=reminder)).strftime('%Y-%m-%d')))
    
    first1 = True
    
    rawOut = args.output
    formattedOut = '.'.join((rawOut.split('.')[:-1])+['formatted.json'])
    
    with Unbuffered(open(rawOut, 'wt')) as out:
        # pp = pprint.PrettyPrinter(indent=2, width=200, sort_dicts=True,
        #                           compact=False, stream=out)
        out.write('[')
        for start, end in intervals:
            payload['start'] = start
            payload['end'] = end
            if first1:
                openBraket = '['
                first1 = False
            else:
                openBraket = ',['

            out.write(openBraket)
            first2 = True
            
            for type in types:
                if first2:
                    openBraket = '['
                    first2 = False
                else:
                    openBraket = ',['

                out.write(openBraket)
                payload['type'] = type
                data = json.dumps(payload)
                out.write(data)
                out.write(',')
                conn.request("POST", "/api", data, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.dumps(json.loads(data.decode("utf-8")))
                out.write(data)
                out.write(']')
                out.flush()

                time.sleep(1)

            out.write(']')
        out.write(']')

    with open(rawOut, 'rt') as inFile:
        with open(formattedOut, 'wt') as outFile:
            json.dump(json.load(inFile), outFile, indent=2)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''
################
Enedis collector
################
''')
    maxDate = (datetime.now()-timedelta(days=(24*30.25)))
    maxDateStr = maxDate.strftime('%Y-%m-%d')
    parser.add_argument('--auth', '-a', metavar='<AUTH>', type=str,
                        help='Authorization token, like mogHR8VzTLwrn...JFxlM '
                             'Get it on: https://enedisgateway.tech',
                        required=True)
    parser.add_argument('--pdlid', '-p', metavar='<PDL_ID>', type=str,
                        help='PDL identifier, like 12345678901234 '
                        'Get it on: '
                        'https://mon-compte-particulier.enedis.fr/compteur/',
                        required=True)
    parser.add_argument('--start-date', '--start_date', '-s',
                        metavar='<START_DATE YYYY-MM-DD>',
                        type=date.fromisoformat, default=None,
                        help='Start date (Default = end-date - 7 days). '
                             f'Must be > {maxDateStr}')
    parser.add_argument('--end-date', '--end_date', '-e',
                        metavar='<END_DATE YYY-MM-DD>',
                        type=date.fromisoformat,
                        default=datetime.now()-timedelta(days=1),
                        help='End date (Default yesterday)')
    parser.add_argument('--output', '-o',
                        metavar='<output file>',
                        type=str,
                        default='enedis.json',
                        help='Output file (Default to enedis.json)')

    args = parser.parse_args()
    if args.start_date is None:
        args.start_date = args.end_date - timedelta(days=7)
    elif datetime.combine(args.start_date, datetime.min.time()) < maxDate:
        args.start_date = maxDate

    run(args)