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
        card_status_num = 0
        c_s = '查询失败！'
        while True:
            card_status = QuanQiuFu().card_status_query(card_no)
            if card_status.get('resp_code') == '0000':
                detail = card_status.get('response_detail')
                card_status = detail.get('card_status')
                if card_status == '00':
                    c_s = '正常'
                elif card_status == '11':
                    c_s = '冻结'
                elif card_status == '99':
                    c_s = '注销'
                elif card_status == '10':
                    c_s = '锁定'
                else:
                    c_s = card_status
                break
            elif card_status_num > 2:
                break
            else:
                card_status_num += 1


    except:
        remain = 0
        c_s = '查询失败！'
    print(card_no, remain, c_s)
    SqlData().update_card_remain('remain', float(remain), card_no)
    SqlData().update_card_info_card_no('status', c_s, card_no)
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
    print(card_info)
    get_card_remain(card_info)
    # print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
