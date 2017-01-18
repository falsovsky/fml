#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import re, sqlite3, datetime, time, os, sys, hashlib
if sys.version_info[0] < 3:
    from urllib2 import build_opener, HTTPError
else:
    from urllib.request import build_opener, HTTPError
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
        mylib.print_console("%d found '.lf %d' for the next one" % (total, position+1))

    sql = 'select id, fml_id, datetime(dt, "unixepoch") as data, msg FROM fml ORDER BY id ASC LIMIT ?,1'
    args = [position-1]
    c = conn.execute(sql, args)
    rows = c.fetchall()[0]
    msg = "%s - #%s, %s" % (rows[3], rows[1], rows[2])
    return msg

def update_records():
    lastts = get_latest_record_ts()
    print("last timestamp on db: %s" % lastts)

    lastpage = "3645"
    total = int(lastpage)

    for page in range(1, int(lastpage)):
        print("scrapping page: %d" % page)

        opener = build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')]
        try:
            response = opener.open('http://www.fmylife.com/?page='+ str(page))
        except HTTPError as err:
            if err.code == 500:
                print("Error 500")
                continue

        html = response.read()
        soup = BeautifulSoup(html, "html.parser")

        if soup.find('article', 'col-xs-12') is None:
            print("reached the end??")
            break

        for article in soup.find_all('article', 'col-xs-12'):
            # pub
            if article.find('div', 'ribbon'):
                continue

            # get id
            link = article.find('a')
            match = re.search(r"_(\d+)\.html", link['href'])
            article_id = match.group(1)

            info = article.find('div', 'text-center').getText()
            r = re.search(r"\w+ (?P<date>\d+ \w+ \d+) (?P<time>\d+:\d+)", info)
            dt = datetime.datetime.strptime(r.group('date') + ' ' + r.group('time'), "%d %B %Y %H:%M")
            ts = str(time.mktime(dt.timetuple()))[:-2]

            msg = article.findAll('a')[1].string
            if msg is None:
                continue
            msg = msg.encode('utf-8').strip()

            if int(ts) < int(lastts):
                return

            try:
                conn.execute('insert into fml (fml_id, dt, msg) values(?, ?, ?)', [article_id, ts, msg])
            except sqlite3.IntegrityError:
                print("Skipping already on DB")
                pass
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
