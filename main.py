import os
import bs4
import json
import pickle
import tweepy
import requests
import settings_log
import logging.config

savefile = "list.pkl"
page_nums = ["0", "1", "2"]
label = {"0":"掲載日", "1":"企業名", "2": "担当者氏名", "3": "業種", "4": "所在地", "5": "電話番号", "100": "内容", "101": "勤務場所", "102": "勤務期間", "103": "勤務時間", "104": "賃金", "105": "募集人数", "106": "交通費", "107": "給与支払", "200": "採用の決め方", "201": "連絡事項", "202": "リンク先", "300": "詳細"}

def get_logger(name):
    logging.config.dictConfig(settings_log.LOGGING_CONF)
    return logging.getLogger(name)

logger = get_logger(__name__)

def scrape_each(info_each):
    info_fix = info_each.find_all("dl")
    dic = {}
    for i in range(len(info_fix)):
        tmp = info_fix[i].find_all("dd")
        for j in range(len(tmp)):
            dic[str(i*100 + j)] = tmp[j].text.strip().replace("\u3000", " ")
    dic["5"] = dic["5"].split("\n")[0]
    return dic

def tweet(content):
    consumer_key = os.environ["CONSUMER_KEY"]
    consumer_secret = os.environ["CONSUMER_SECRET"]
    access_token = os.environ["ACCESS_TOKEN"]
    access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    api.update_status(content)

#make list of infomation on web site
list_tod = []
for page_num in page_nums:
    url = "https://www.hokudai-job.com/list.php?list_flag="  + page_num
    try:
        r = requests.get(url, timeout=3.5)
    except Exception as e:
        logger.error("Error at requests")
        logger.exception("Raise Exception : %s", e)
    r.encoding = r.apparent_encoding
    soup = bs4.BeautifulSoup(r.text)
    
    info_recruit = soup.find("ul", attrs={"id": "recruit"})
    info_each = info_recruit.find_all("li")
    
    for detail in info_each:
        dic = scrape_each(detail)
        dic["300"] = url
        list_tod.append(dic)

with open(savefile, "wb") as f:
    pickle.dump(list_tod, f, -1)

list_yest = []
with open(savefile, 'rb') as f:
    list_yest = pickle.load(f)

#check if tweeted the infomation
list_tweet = []
for article in list_tod:
    if article not in list_yest:
        list_tweet.append(article)

#setting detail of tweet
list_label_to_tweet = ["1", "3", "100", "104", "300"]
lim_len = {"1": 15, "3": 15, "100": 40, "101": 20, "103": 20, "104": 15, "300": 60}

#tweet
for detail in list_tweet:
    content = ""
    for lab in list_label_to_tweet:
        content += label[lab] + "\n"
        content += "　" + detail[lab][:lim_len[lab]]
        if len(detail[lab]) >= lim_len[lab]:
            content += "_"
        content += "\n"
    try:
        tweet(content)
        logger.info("success to tweet")
        logger.info("msg : %s", content)
    except Exception as e:
        logger.error("Error at tweet")
        logger.exception("Raise Exception : %s", e)
