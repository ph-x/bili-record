from pip._vendor import requests
import json
import time
import threading
import datetime
import os
import sys
import sched
threads = []
scheduler = sched.scheduler(time.time, time.sleep)
exit = threading.Event()
def log(name, time, play):
    with open('listened.log', 'a') as logfile:
        logfile.write(str(name) + '\t' + str(time) + '\t' + str(play) + '\n')
def get_submited_videos(uid, pagesize=40, page=1):
    parameters = {'mid' : uid, 'pagesize' : pagesize, 'page' : page}
    base_url = 'http://space.bilibili.com/ajax/member/getSubmitVideos'
    try:
        response = requests.get(url=base_url, params = parameters)
    except:
        return get_submited_videos(uid, pagesize, page)
    return response.json()['data']
def get_user_latest_i_videos(uid, i):
    return get_submited_videos(uid, i, 1)
def get_user_latest_video(uid):
    return get_submited_videos(uid, 1, 1)

def get_video_stat(aid):
    parameters = {'aid' : aid}
    base_url = 'http://api.bilibili.com/archive_stat/stat'
    try:
        response = requests.get(url=base_url, params = parameters)
    except:
        return get_video_stat(aid)
    return response.json()['data']

def fetch_video_info(aid, time_gap):
    data = get_video_stat(aid)
    format = {3600 : '1h', 86400 : '1d', 604800 : '1w'}
    log(data['aid'], format[time_gap], data['view'])

def run_at_abs_time(abs_time, function, args):
    now = time.time()
    t = threading.Timer(abs_time - now, function, args)
    if now <= abs_time:
        t.setDaemon(True)
        t.start()
        threads.append(t)
    else:
        log('Error', 'time', 'past')
def watch_new_video__(video):
    time_gap = [3600, 86400, 604800]
    create_time = video['created']
    for gap in time_gap:
        t = run_at_abs_time(create_time + gap, fetch_video_info, (video['aid'], gap, ))
def watch_new_videos():
    with open('listened.json', 'r+') as jfile:
        listened = json.load(jfile)
        for user in listened['ulist']:
            response = get_user_latest_video(user['uid'])
            i = response['pages'] - user['vnum']
            if i <= 0:
                continue
            else:
                user['vnum'] = response['pages']
                user['latest'] = response['vlist'][0]['aid']

                response = get_user_latest_i_videos(user['uid'], i)
                vlist = response['vlist']
                for video in vlist:
                    listened['vlist'].append(video['aid'])
                    watch_new_video__(video)
        #cover json file
        jfile.seek(0, os.SEEK_SET)
        json.dump(listened, jfile)

def main(t):
    watch_new_videos()
    while not exit.is_set():
        print('running'+'\t'+str(datetime.datetime.now()))
        sys.stdout.flush()
        scheduler.enter(t, 1, watch_new_videos, ())
        scheduler.run()
"""def quit(signo, _frame):
    print("Interrupted by %d, shutting down" % signo)
    exit.set()


import signal
for sig in ('TERM', 'INT'):
    signal.signal(getattr(signal, 'SIG'+sig), quit);
"""
main(2700)
