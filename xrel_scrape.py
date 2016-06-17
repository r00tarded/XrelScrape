import gevent
from gevent.queue import *
import gevent.monkey
import urllib2
from bs4 import BeautifulSoup #pip install BeautifulSoup4
from timeit import default_timer as timer
import datetime
import random
from fake_useragent import UserAgent #pip install fake-useragent
from progress.bar import Bar #pip install progress
import csv

now = datetime.datetime.now()
gevent.monkey.patch_all()
q = gevent.queue.JoinableQueue()


def check_if_str_in_list(some_list,bad):
    for s in some_list:
        for item in bad:
            if item in s:
                return True 
    return False

                
def parse_titles(soup,cat):
    titles = []
    for tag in soup.findAll("a", { "class" : "sub_link"}):
        try:
            tag = str(tag)
            if 'title="' in tag:
                title = tag.split('title="')[1].split('"')[0]
            else:
                title = tag.split('_title')[1]
                title = title.split('">')[1].split('</span>')[0]
            if cat == 'apps-win':
                if '.' in title:
                    tit = title.lower().split('.')
                elif '_' in title:
                    tit = title.lower().split('_')
                flag = ['x64','x32','win32','win32']
                neg = ['linux','mac','lxn64','linux64','macosx64','lnx64-xforce']
                if check_if_str_in_list(tit,neg) == False:
                    if check_if_str_in_list(tit,flag) == True:
                        titles.append(title)  
            else:
                titles.append(title)
        except:
            pass
    return titles

def parse_sizes(soup):
    sizes = []
    for tag in soup.findAll("span", { "class" : "sub"}):
        try:
            if 'MB' in str(tag):
                size = str(tag).split('>')[1].split('<')[0].split(' ')[0]
                sizes.append(str(size))
        except:
            pass
    return sizes

def parse_date(soup):
    dors = []
    for tag in soup.findAll("div", { "class" : "release_date"}):
        try:
            dor = str(tag.text.strip())
            dor = dor[:8]+'-'+dor[8:-4]
            dors.append(dor)
        except:
            pass
    return dors

def get_qer(cat):
        quer = {'movies':'movies-release-list','top-movies':'movie-topmovie-release-list',
            'console':'console-release-list','games':'game-windows-release-list',
            'apps-win':'apps-release-list','apps':'apps-release-list','tv':'tv-release-list',
            'english':'english-release-list','hotstuff':'hotstuff-release-list',
            'xxx':'xxx-xxx-release-list','movies-p2p':'p2p/15-movie/releases',
            'games-p2p':'p2p/9-games/releases','apps-p2p':'p2p/12-software',
            'console-p2p':'p2p/10-console/releases','tv-p2p':'p2p/16-tv/releases',
            'apps-p2p':'p2p/12-software/releases'}
        return str(quer[cat])
    
def parse_nextpage(cat,date):
    try:
        soup = get_html(2,cat,date)
        html = soup.find("div", { "class" : "pages clearfix"})
        soup = BeautifulSoup(str(html), "html.parser")
        return int(soup.findAll("a", { "class" : "page"})[-1].text)
    except:
        return 1
    

def get_html(page,cat,date):
    if date == 'now':
        date = str(now.strftime("%Y-%m-%d %H:%M")[:-9])
        print date
    url = "https://www.xrel.to/"+ get_qer(cat) +".html?archive="+date+"&page="+str(page)
    ua = UserAgent().random
    req = urllib2.Request(url, headers={'User-Agent': ua,'Accept':'*/*'})
    html = urllib2.urlopen(req).read()
    soup = BeautifulSoup(html, "html.parser")
    return soup

def scrape(page,cat,date):
    soup = get_html(page,cat,date)
    rl_name = parse_titles(soup,cat)
    mb = parse_sizes(soup)
    date = parse_date(soup)
    return zip(rl_name, mb,date)

def worker():
    global names
    names = []
    while not q.empty():
        t = q.get()
        try:
            r = scrape(t[0],t[1],t[2])
            names.extend(r)
        except:
            q.put(t, timeout=3)
        finally:
            gevent.sleep(random.uniform(0.001,0.005))
            bar.next()

def loader(cat,date):
    global bar
    pcount = parse_nextpage(cat,date)+1
    print ""
    bar = Bar('Processing page', max=pcount-1)
    for i in range(1,pcount):
        q.put((i,cat,date), timeout=3)

def asynchronous():
    threads = []
    for i in range(workers):
        threads.append(gevent.spawn(worker))
    start = timer()
    gevent.joinall(threads,raise_error=True)
    bar.finish()
    end = timer()
    print ""
    print "Time passed: " + str(end - start)[:6]


cat = 'apps'
date = 'now'
workers = 24
gevent.spawn(loader(cat,date)).join()
asynchronous()

print len(set(names))

with open(cat+'.txt', "wb") as the_file:
    csv.register_dialect("custom", delimiter=",", skipinitialspace=True)
    writer = csv.writer(the_file, dialect="custom")
    writer.writerow((['release','size(mb)','date']))
    for tup in names:
        writer.writerow(tup)