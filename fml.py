#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib2, re, sqlite3, datetime, time, os, sys
import mylib

scriptpath = os.path.dirname(os.path.realpath(__file__))
conn = sqlite3.connect(scriptpath + '/fml.db')
conn.text_factory = str
conn.row_factory = sqlite3.Row

def get_latest_record_ts():
    sql = 'select max(dt) from fml'
    c = conn.execute(sql)
    zbr = c.fetchone()
    if zbr[0] is None:
        return 0
    else:
        data = zbr[0]
        return int(data)

def get_random():
    c = conn.execute('select fml_id, datetime(dt, "unixepoch") as data, msg from fml ORDER BY RANDOM() LIMIT 1;')
    rows = c.fetchall()[0]
    msg = "%s" % (rows[2])
    return msg

def update_records():
    print "updating..."

    lastts = get_latest_record_ts()
    print "lastts: %s" % lastts

    response = urllib2.urlopen('http://www.fmylife.com')
    html = response.read()
    soup = BeautifulSoup(html)
    lastpage = str(soup.find('ul', 'left').find_all('li')[-1:][0].string)

    total = int(lastpage)
    print "total pages: %s" % total

    for page in range(0, int(lastpage)):
        print page

        response = urllib2.urlopen('http://www.fmylife.com/?page='+ str(page))
        html = response.read()
        soup = BeautifulSoup(html)

        for message_block in soup.find_all('div', 'post article'):
            id = message_block['id']
            dt_str = str(message_block.find('div', 'right_part').find_all('p')[1])
            r = re.search(r"On (?P<date>\d+/\d+/\d+) at (?P<time>\d+:\d+(am|pm))", dt_str)
            dt = datetime.datetime.strptime(r.group('date') + ' ' + r.group('time'), "%m/%d/%Y %I:%M%p")
            ts = str(time.mktime(dt.timetuple()))[:-2]

            msg = ""

            for message_line in message_block.find_all('a', 'fmllink'):
                if message_line.string is not None:
                    msg = msg + message_line.string.encode('utf-8').strip() + "\n"

            msg = msg.strip()

        if int(ts) <= int(lastts):
            raise Exception("No new ones")

        conn.execute('insert into fml (fml_id, dt, msg) values(?, ?, ?)', [id, ts, msg])
        conn.commit()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        mylib.print_console(get_random())

    if len(sys.argv) > 1:
        if sys.argv[1] == 'cron':
            try:
                update_records()
            except Exception:
                print "No more updates"
