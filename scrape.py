# -*- coding: utf-8 -*-
import unicodecsv
from lxml import html
from retrying import retry
import re
import sys
reload(sys)
sys.setdefaultencoding('UTF8')


@retry(wait_random_min=5000, wait_random_max=10000)
def scrape_thread(thread):
    print thread
    t = html.parse(thread)
    title = t.xpath('//span[@class="ag_title"]/text()')[0]
    # print title
    qid = re.findall('/(\d*)-', thread)[0]
    for br in t.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    reply_to = " "
    posters=set()

    for id, post in enumerate(t.xpath('//*[@class="ag_postrow_container"]')):
        inferred_replies = set()

        if id > 0:
            reply_to = qid+"_top"
        poster = post.xpath('.//dt[@class="ag_username"]/text()')[0]
        date = post.xpath('.//div[@class="ag_postdate"]/text()')[0]
        content = post.xpath('.//div[@class="ag_postmsg"]')[0].text_content()
        for p in posters:
            if p in content:
                inferred_replies.add(p)
        posters.add(poster)
        yield {'qid':qid, 'title':title,
               'poster': poster, 'date': date,
               'reply_to': reply_to, 'content': content,
               'inferred_replies': ' | '.join(inferred_replies)}

def scrape_sub(sub):
    url = base+sub.attrib['href']
    sub = html.parse(url)
    for thread in sub.xpath('//div[@class="ag_forumrow"]//div[@class="ag_forumDesc_pages"]/a[last()]'):
        thread_pages = int(thread.text.strip())
        normal = base + re.findall('(.*/).*$', thread.attrib['href'])[0]
        replies = []
        for reply in scrape_thread(normal):
            replies.append(reply)
        if thread_pages > 1:
            for thread_page in xrange(1, thread_pages):
                for reply in scrape_thread(normal+'?p='+str(thread_page)):
                    replies.append(reply)
        for i, reply in enumerate(replies):
            if i > 0:
                reply_to = reply['qid'] + "_top"
                unique_id = reply['qid'] + '_' + str(i - 1)
            else:
                reply_to = " "
                unique_id = reply['qid'] + '_top'
            w.writerow([unique_id, reply['qid'], i - 1, reply['title'], reply['poster'],
                        reply['date'], reply_to, reply['content'],
                        ' | '.join(reply['inferred_replies']), subforum])
        f.flush()

base = "http://www.healthyplace.com"
start = html.parse("http://www.healthyplace.com/forum/")
f = open('healthyplace.csv', 'w')
w = unicodecsv.writer(f, encoding='utf-8', lineterminator='\n')
w.writerow(['uniqueID', 'qid', 'localID', 'title', 'poster', 'date', 'replyTo', 'content', 'infered_replies', 'subforum'],)


for sub in start.xpath('//div[@class="ag_forumName"]/a[2]'):
    subforum = sub.text
    scrape_sub(sub)
