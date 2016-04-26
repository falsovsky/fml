#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib2, re, sqlite3, datetime, time, os, sys, hashlib
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
    msg = "%s - #%s, %s" % (rows[2], rows[0], rows[1])
    return msg

def find_record(find, position = 1):
    if position <= 0:
        position = 1
    sql = 'select count(1) from fml where msg like ? OR fml_id = ?'
    args = ['%'+find+'%', find.translate(None, '#')]
    c = conn.execute(sql, args)
    total = c.fetchone()[0]
    if total == 0 or int(position) > int(total):
        mylib.print_console("Not found")
        sys.exit()
    if total > 1 and position < total:
        mylib.print_console("%d found '.ff %s %d' for the next one" % (total, find, position+1))

    sql = 'select id, fml_id, datetime(dt, "unixepoch") as data, msg from fml WHERE msg like ? OR fml_id = ? ORDER BY data DESC LIMIT ?,1'
    args = ['%'+find+'%', find.translate(None, '#'), position-1]
    c = conn.execute(sql, args)
    rows = c.fetchall()[0]
    msg = "%s - #%s, %s" % (rows[3], rows[1], rows[2])
    return msg

def list_record(position = 1):      
    if position <= 0:
        position = 1
    sql = 'select count(1) from fml'
    c = conn.execute(sql)
    total = c.fetchone()[0]
    if total == 0 or int(position) > int(total):
        mylib.print_console("Not found")
        sys.exit()
    if total > 1 and position < total:
        mylib.print_console("%d found '.fl %d' for the next one" % (total, position+1))

    sql = 'select id, fml_id, datetime(dt, "unixepoch") as data, msg FROM fml ORDER BY data DESC LIMIT ?,1'
    args = [position-1]
    c = conn.execute(sql, args)
    rows = c.fetchall()[0]
    msg = "%s - #%s, %s" % (rows[3], rows[1], rows[2])
    return msg

def update_records():
    lastts = get_latest_record_ts()
    print "last timestamp on db: %s" % lastts

    lastpage = "9000"
    total = int(lastpage)

    for page in range(0, int(lastpage)):
        print "scrapping page: %d" % page

        response = urllib2.urlopen('http://www.fmylife.com/?page='+ str(page))
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")

        if soup.find('div', 'article') is None:
            print "reached the end??"
            break

        for article in soup.find_all('div', 'article'):
            if "is-historical" in article["class"]:
                continue

            id = article['id']
            date = article.find('div', 'date').find('p').getText()
            r = re.search(r"(?P<date>\d+/\d+/\d+) at (?P<time>\d+:\d+[a|p]m)", date)
            dt = datetime.datetime.strptime(r.group('date') + ' ' + r.group('time'), "%m/%d/%Y %I:%M%p")
            ts = str(time.mktime(dt.timetuple()))[:-2]

            msg = article.find('p', 'content').find('a').string
            if msg is None:
                continue

            msg = msg.encode('utf-8').strip()

            if int(ts) <= int(lastts):
                return

            conn.execute('insert into fml (fml_id, dt, msg) values(?, ?, ?)', [id, ts, msg])
            conn.commit()

def get_magic_random(s):
    sql = 'select count(1) from fml'
    c = conn.execute(sql)
    total = c.fetchone()[0]

    h = hashlib.sha256(s).hexdigest()
    n = int(h, 16)
    myid = n % total

    c = conn.execute('select id, fml_id, datetime(dt, "unixepoch"), msg from fml where id = ?;', [myid])
    rows = c.fetchall()[0]
    msg = "%s - #%s, %s" % (rows[3], rows[1], rows[2])
    return msg

if __name__ == "__main__":
    if len(sys.argv) == 1:
        mylib.print_console(get_random())
    if len(sys.argv) > 1:
        if sys.argv[1] == 'cron':
            mylib.print_console('Updating...')
            update_records()
        elif sys.argv[1] == 'find':
            if len(sys.argv) == 2:
                mylib.print_console(".ff: find argument required")
                sys.exit()
            try:
                if (len(sys.argv) > 3):
                    pos = int(sys.argv[-1])
                    msg = ' '.join(sys.argv[2:][:-1])
                else:
                    msg = sys.argv[2]
                    pos = 0
            except ValueError:
                pos = 0
                msg = ' '.join(sys.argv[2:])
            #print "msg: '%s' pos: '%d'" % (msg , pos)
            mylib.print_console(find_record(msg, pos))
        elif sys.argv[1] == 'magia':
            if len(sys.argv) > 2:
                mylib.print_console(get_magic_random(''.join(sys.argv[2:])))
            else:
                mylib.print_console(get_random())
        elif sys.argv[1] == 'lista':
            if len(sys.argv) > 2:
                try:
                    pos = int(sys.argv[2])
                except ValueError:
                    pos = 0
                mylib.print_console(list_record(pos))
            else:
                mylib.print_console(list_record())
