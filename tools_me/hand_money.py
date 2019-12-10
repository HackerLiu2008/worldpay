from os import path
import openpyxl
import os
import xlrd
from mysql_tools import SqlData
from openpyxl.drawing.image import Image
from xlutils.copy import copy

from other_tools import sum_code, xianzai_time
from parameter import TRANS_TYPE, DO_TYPE
from tools_me.mysql_tools import SqlData
from helen import QuanQiuFu


card_list = SqlData().search_card_info_admin('WHERE account_id=45')
for card_info in card_list:
    card_no = card_info.get('card_no').strip()
    pay_passwd = card_info.get('pay_passwd')
    resp = QuanQiuFu().query_card_info(card_no)
    if resp.get('resp_code') == '0000':
        detail = resp.get('response_detail')
        freeze_fee_all = detail.get('freeze_fee_all')
        balance = detail.get('balance')
        f_freeze = int(freeze_fee_all) / 100
        f_balance = int(balance) / 100
        remain = round(f_balance - f_freeze, 2)

        if remain > 1:
            data = remain - 1
            refund_money = str(round(float(data) * 100))
            resp = QuanQiuFu().trans_account_cinsume(card_no, pay_passwd, refund_money)
            resp_code = resp.get('resp_code')
            resp_msg = resp.get('resp_msg')
            if resp_code == "0000":
                user_id = 45
                refund = SqlData().search_user_field('refund', user_id)
                hand_money = round(refund * float(data), 2)
                do_money = round(float(data) - hand_money, 2)

                before_balance = SqlData().search_user_field('balance', user_id)
                # 更新账户余额
                SqlData().update_balance(do_money, user_id)
                balance = SqlData().search_user_field('balance', user_id)

                # 将退款金额转换为负数
                do_money = do_money - do_money * 2
                n_time = xianzai_time()
                SqlData().insert_account_trans(n_time, TRANS_TYPE.IN, DO_TYPE.REFUND, 1, card_no, do_money, hand_money,
                                               before_balance,
                                               balance, user_id)

                # 更新客户充值记录
                pay_num = sum_code()
                t = xianzai_time()
                SqlData().insert_top_up(pay_num, t, do_money, before_balance, balance, user_id, '退款')




# print(os.path.abspath(''))
#
# file_path = "C:\\Users\\Think\\Desktop\\88888.xls"
#
#
# data = xlrd.open_workbook(file_path, encoding_override='utf-8')
# table = data.sheets()[0]
# nrows = table.nrows  # 行数
# ncols = table.ncols  # 列数
# row_list = list()
# method = 'c'
# if method == 'r':
# row_list = [table.row_values(i) for i in range(0, nrows)]  # 所有行的数据
# elif method == 'c':
# col_list = [table.col_values(i) for i in range(0, ncols)]  # 所有列的数据
# card_list = col_list[0][1:]

'''
wb = openpyxl.load_workbook(file_path)
wb1 = wb.active
img_path = "G:\\world_pay\\static\\pay_pic\\大龙_20191107101121e40ed.png"
img = Image(img_path)
img.width = 400
img.height = 400
wb1.add_image(img, 'K1')
save_path = file_path
wb.save(save_path)
'''
