# coding:utf-8
from threading import Lock
import threading
from helen import QuanQiuFu
from mysql_tools import SqlData

lock = Lock()


def loop(card_info):
    card_no = card_info.get('card_no').strip()
    try:
        search_num = 0
        while True:
            resp = QuanQiuFu().query_card_info(card_no)
            re_code = resp.get('resp_code')
            if re_code == '0000':
                detail = resp.get('response_detail')
                freeze_fee_all = detail.get('freeze_fee_all')
                balance = detail.get('balance')
                f_freeze = int(freeze_fee_all) / 100
                f_balance = int(balance) / 100
                remain = round(f_balance - f_freeze, 2)
                break
            elif re_code == '0054':
                remain = 0
                break
            elif search_num > 2:
                remain = 0
                break
            else:
                search_num += 1
    except:
        remain = 0
    SqlData().update_card_remain('remain', float(remain), card_no)
    return


def get_card_remain(loops):
    lock.acquire()
    while True:
        loops_len = len(loops)
        num = 5
        if loops_len < 5:
            num = loops_len
        threads = []
        for i in range(num):
            data = loops.pop()
            t = threading.Thread(target=loop, args=(data, ))
            threads.append(t)
        for i in threads:  # start threads 此处并不会执行线程，而是将任务分发到每个线程，同步线程。等同步完成后再开始执行start方法
            i.start()
        for i in threads:  # jion()方法等待线程完成
            i.join()
        if len(loops) == 0:
            break
    lock.release()
    return


if __name__ == '__main__':
    # print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    card_info = SqlData().search_card_info_admin('WHERE card_no is not null')
    get_card_remain(card_info)
    # print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
