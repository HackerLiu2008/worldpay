import json
import logging
import operator
import re
import uuid
import xlrd
from config import cache
from send_email import send
from tools_me.other_tools import xianzai_time, login_required, check_float, make_name, sum_code, save_file, is_chinese, \
    verify_code, Base64Code, get_day_after, verify_login_time
from tools_me.parameter import RET, MSG, TRANS_STATUS, TRANS_TYPE, DO_TYPE, DIR_PATH
from tools_me.helen import QuanQiuFu
from tools_me.remain import get_card_remain
from . import user_blueprint
from tools_me.send_sms.send_sms import CCP
from flask import render_template, request, jsonify, session, g, redirect, send_file
from tools_me.mysql_tools import SqlData


@user_blueprint.route('/push_log/', methods=['GET'])
@login_required
def push_log():
    try:
        user_id = g.user_id
        page = request.args.get('page')
        limit = request.args.get('limit')
        range_time = request.args.get('range_time')
        card_no = request.args.get('card_no')
        trans_type = request.args.get('trans_type')
        if range_time:
            start_time = range_time.split(" - ")[0]
            end_time = range_time.split(" - ")[1] + ' 23:59:59'
            time_sql = " AND timestamp BETWEEN '" + start_time + "' AND '" + end_time + "'"

            card_sql = ""
            if card_no:
                card_sql = " AND card_no LIKE '%" + card_no + "%'"

            trans_sql = ""
            if trans_type:
                trans_sql = " AND trans_type ='" + trans_type + "'"

            sql = time_sql + card_sql + trans_sql
        else:
            start_index = (int(page) - 1) * int(limit)
            sql = ' ORDER BY push_log.id desc limit ' + str(start_index) + ", " + limit + ';'

        results = dict()
        results['msg'] = MSG.OK
        results['code'] = RET.OK
        info = SqlData().search_user_push(user_id, sql)
        if not info:
            results['msg'] = MSG.NODATA
            return jsonify(results)
        task_info = info
        page_list = list()

        if 'limit' in sql:
            s = 'push_log WHERE account_id={}'.format(user_id)
            results['data'] = task_info
        else:
            # 分页显示
            task_info = list(reversed(task_info))
            for i in range(0, len(task_info), int(limit)):
                page_list.append(task_info[i:i + int(limit)])
            results['data'] = page_list[int(page) - 1]
            s = 'push_log WHERE account_id={}'.format(user_id) + sql
        results['count'] = SqlData().search_table_count(s)
        return jsonify(results)
    except Exception as e:
        logging.error('查询卡交易推送失败:' + str(e))
        return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@user_blueprint.route('/xls_top/', methods=['POST'])
@login_required
def xls_top():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            filename = file.filename
            file_path = save_file(file, filename, DIR_PATH.XLS_PATH)
            data = xlrd.open_workbook(file_path, encoding_override='utf-8')
            table = data.sheets()[0]
            nrows = table.nrows  # 行数
            ncols = table.ncols  # 列数
            row_list = [table.row_values(i) for i in range(0, nrows)]  # 所有行的数据
            col_list = [table.col_values(i) for i in range(0, ncols)]  # 所有列的数据

            # 定义返回信息
            results = {'code': '', 'msg': ''}
            user_id = g.user_id

            # 判断是否填写充值信息或者大于一百次充值
            if len(row_list) <= 1 or len(row_list) > 101:
                results['code'] = RET.OK
                results['msg'] = '请规范填写内容后上传!(单次批量充值不能超过100次)'
                return jsonify(results)

            # 判断总充值金额是否满足本次充值总额
            money_list = col_list[1][1:]
            sum_money = 0
            for m in money_list:
                if not check_float(m):
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '充值金额不能为小数: ' + str(m)
                    return jsonify(results)
                try:
                    sum_money += int(m)
                except:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '请填写正确的充值金额!'
                    return jsonify(results)
            balance = SqlData().search_user_field('balance', user_id)
            if sum_money > balance:
                results['code'] = RET.SERVERERROR
                results['msg'] = '账户余额不足,请充值后重试!'
                return jsonify(results)

            # 判断卡号是否规范!判断卡号是否属于该用户!判断充值金额是否符合要求
            _card = row_list[1:]
            for card_list in _card:
                card_no = card_list[0].strip()
                if len(card_no) != 16:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '卡号不规范: ' + card_no
                    return results
                account_id = SqlData().search_card_field('account_id', card_no)
                if not account_id or account_id != user_id:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '没有该卡号: ' + card_no
                    return results

            # 给每张卡做充值
            for card_list in _card:
                card_no = card_list[0].strip()
                top_money = int(card_list[1])
                balance = SqlData().search_user_field('balance', user_id)
                if float(top_money) > balance:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '充值卡号: ' + card_no + ", 失败! 账户余额不足!"
                    return jsonify(results)
                money = str(int(top_money) * 100)

                # 防止API异常,异常则重复充值3次,直到充值成功,3次仍是失败则退出本次充值
                top_num = 0
                while True:
                    resp = QuanQiuFu().trans_account_recharge(card_no, money)
                    resp_code = resp.get('resp_code')
                    if resp_code == '0000':
                        top_money = int(top_money)
                        # 查询账户操作前的账户余额
                        before_balance = SqlData().search_user_field('balance', user_id)
                        # 计算要扣除多少钱
                        do_money = top_money - top_money * 2
                        # 直接更新账户余额,不计算理论余额,用sql更新本次操作费用
                        SqlData().update_balance(do_money, user_id)
                        # 查询扣除后的余额
                        balance = SqlData().search_user_field('balance', user_id)
                        n_time = xianzai_time()
                        SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.TOP_UP, 1, card_no, float(top_money),
                                                       0, before_balance,
                                                       balance, user_id)
                        break
                    elif top_num > 2:
                        resp_msg = resp.get('resp_msg')
                        s = '充值卡余额失败,状态码: ' + resp_code + ',信息: ' + resp_msg
                        logging.error(s)
                        results['code'] = RET.SERVERERROR
                        results['msg'] = "卡号: " + card_no + ", 充值是失败!请尝试单笔充值!"
                        return jsonify(results)
                    else:
                        top_num += 1
            results['code'] = RET.OK
            results['msg'] = MSG.OK
            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            results = {'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR}
            return jsonify(results)


@user_blueprint.route('/download/', methods=['GET'])
@login_required
def xls_download():
    response = send_file(DIR_PATH.DOWNLOAD)
    return response


@user_blueprint.route('/make_up/', methods=['GET'])
@login_required
def make_up():
    try:
        user_id = g.user_id
        sql = "WHERE cvv='' OR expire='' AND account_id={}".format(str(user_id))
        info = SqlData().search_card_info_admin(sql)
        if not info:
            return jsonify({'code': RET.OK, 'msg': '无卡缺失信息!'})
        for i in info:
            card_no = i.get('card_no')
            card_no = card_no.strip()
            resp_card_info = QuanQiuFu().query_card_info(card_no)
            if resp_card_info.get('resp_code') != '0000':
                expire_date = ''
                card_verify_code = ''
            else:
                re_de = resp_card_info.get('response_detail')
                expire_date = re_de.get('expire_date')
                card_verify_code = re_de.get('card_verify_code')
            SqlData().update_card_info_card_no('cvv', card_verify_code, card_no)
            SqlData().update_card_info_card_no('expire', expire_date, card_no)
        return jsonify({'code': RET.OK, 'msg': MSG.OK})
    except Exception as e:
        logging.error(str(e))
        return jsonify({'code': RET.OK, 'msg': MSG.SERVERERROR})


@user_blueprint.route('/card_lock/', methods=['POST'])
@login_required
def card_lock():
    try:
        card_no = request.args.get('card_no')
        resp = QuanQiuFu().card_status_query(card_no)
        resp_code = resp.get('resp_code')
        if resp_code != "0000":
            return jsonify({'code': RET.SERVERERROR, 'msg': '服务器繁忙请稍后在试!'})
        resp_detail = resp.get('response_detail')
        card_status = resp_detail.get('card_status')
        pay_passwd = SqlData().search_card_field('pay_passwd', card_no)
        if card_status == "00":
            # 挂失
            do_type = DO_TYPE.CARD_LOCK
        elif card_status == '11':
            # 解挂
            do_type = DO_TYPE.CARD_OPEN
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '服务器繁忙请稍后在试!'})
        resp = QuanQiuFu().card_loss(card_no, pay_passwd, do_type)
        resp_code = resp.get('resp_code')
        if resp_code == '0000':
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '服务器繁忙请稍后在试!'})
    except Exception as e:
        logging.error(str(e))
        return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@user_blueprint.route('/refund/', methods=['POST'])
@login_required
def refund_balance():
    try:
        data = json.loads(request.form.get('data'))
        card_no = json.loads(request.form.get('card_no'))
        pay_passwd = SqlData().search_card_field('pay_passwd', card_no)
        if "-" in str(data):
            return jsonify({'code': RET.SERVERERROR, 'msg': '请输入正确金额!'})
        refund_money = str(round(float(data) * 100))
        resp = QuanQiuFu().trans_account_cinsume(card_no, pay_passwd, refund_money)
        resp_code = resp.get('resp_code')
        resp_msg = resp.get('resp_msg')
        results = {"code": RET.OK, "msg": MSG.OK}
        if resp_code == "0000":
            user_id = g.user_id
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

            results['msg'] = resp_msg
        else:
            resp_msg = resp.get('resp_msg')
            s = '卡余额领回失败,状态码: ' + resp_code + ',信息: ' + resp_msg
            logging.error(s)
            results['code'] = RET.SERVERERROR
            results['msg'] = resp_msg
        return jsonify(results)
    except Exception as e:
        logging.error(str(e))
        results = {"code": RET.SERVERERROR, "msg": MSG.SERVERERROR}
        return jsonify(results)


@user_blueprint.route('/account_trans/', methods=['GET'])
@login_required
def account_trans():
    page = request.args.get('page')
    limit = request.args.get('limit')

    time_range = request.args.get('time_range')
    card_num = request.args.get('card_num')
    time_sql = ""
    card_sql = ""
    if time_range:
        min_time = time_range.split(' - ')[0]
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        time_sql = "AND do_date BETWEEN " + "'" + min_time + "'" + " and " + "'" + max_time + "'"
    if card_num:
        card_sql = "AND card_no LIKE '%" + card_num + "%'"

    user_id = g.user_id
    task_info = SqlData().search_account_trans(user_id, card_sql, time_sql)
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    if len(task_info) == 0:
        results['MSG'] = MSG.NODATA
        return jsonify(results)
    page_list = list()
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(task_info)
    return jsonify(results)


@user_blueprint.route('/top_up/', methods=['POST'])
@login_required
def top_up():
    data = json.loads(request.form.get('data'))
    user_id = g.user_id
    card_no = data.get('card_no')
    top_money = data.get('top_money')
    if not check_float(top_money):
        results = {"code": RET.SERVERERROR, "msg": "充值金额不能为小数!"}
        return jsonify(results)
    balance = SqlData().search_user_field('balance', user_id)
    if float(top_money) > balance:
        results = {"code": RET.SERVERERROR, "msg": "账户余额不足!"}
        return jsonify(results)
    money = str(int(top_money) * 100)
    resp = QuanQiuFu().trans_account_recharge(card_no, money)
    resp_code = resp.get('resp_code')
    if resp_code == '0000':
        top_money = int(top_money)
        # 查询账户操作前的账户余额
        before_balance = SqlData().search_user_field('balance', user_id)
        # 计算要扣除多少钱
        do_money = top_money - top_money * 2
        # 直接更新账户余额,不计算理论余额,用sql更新本次操作费用
        SqlData().update_balance(do_money, user_id)
        # 查询扣除后的余额
        balance = SqlData().search_user_field('balance', user_id)
        n_time = xianzai_time()
        SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.TOP_UP, 1, card_no, float(top_money), 0, before_balance,
                                       balance, user_id)
        return jsonify({"code": RET.OK, "msg": "充值成功!请刷新界面!"})
    else:
        resp_msg = resp.get('resp_msg')
        s = '充值卡余额失败,状态码: ' + resp_code + ',信息: ' + resp_msg
        logging.error(s)
        return jsonify({"code": RET.SERVERERROR, "msg": "充值失败!请联系服务商解决!"})


@user_blueprint.route('/create_some/', methods=['POST'])
@login_required
# @choke_required
def create_some():

    # print(session.get('create'))
    data = json.loads(request.form.get('data'))
    card_num = data.get('card_num')
    name_status = data.get('n')
    content = data.get('content')
    limit = data.get('limit')
    label = data.get('label')
    user_id = g.user_id
    user_data = SqlData().search_user_index(user_id)
    create_price = user_data.get('create_card')
    min_top = user_data.get('min_top')
    max_top = user_data.get('max_top')
    balance = user_data.get('balance')

    card_num = int(card_num)
    if card_num > 20:
        results = {"code": RET.SERVERERROR, "msg": "批量开卡数量不得超过20张!"}
        return jsonify(results)

    if name_status == "write":
        name_list = content.split("|")
        if len(name_list) < card_num:
            results = {"code": RET.SERVERERROR, "msg": "名字数量小于建卡数量!"}
            return jsonify(results)
    else:
        name_list = make_name(card_num)

    if not check_float(limit):
        results = {"code": RET.SERVERERROR, "msg": "充值金额不能为小数!"}
        return jsonify(results)
    sum_money = card_num * int(limit) + card_num * create_price

    # 本次开卡需要的费用,计算余额是否充足
    if sum_money > balance:
        results = {"code": RET.SERVERERROR, "msg": "本次消费金额:" + str(sum_money) + ",账号余额不足!"}
        return jsonify(results)

    # 计算充值金额是否在允许范围
    if not min_top <= int(limit) <= max_top:
        results = {"code": RET.SERVERERROR, "msg": "充值金额不在允许范围内!"}
        return jsonify(results)

    act_count = SqlData().search_activation_count()

    if act_count < card_num:
        results = {"code": RET.SERVERERROR, "msg": "请联系服务商添加库存!"}
        return jsonify(results)

    # 查询是否有免费开卡的数量(如果没有,就不必在循环开卡的时候反复查询,浪费资源)
    free = SqlData().search_user_field('free', user_id)

    try:
        for i in range(card_num):
            # my_lock.acquire()
            activation = SqlData().search_activation()
            if not activation:
                return jsonify({"code": RET.SERVERERROR, "msg": "请联系服务商添加库存!"})
            SqlData().update_card_info_field('card_name', 'USING', activation)
            # my_lock.release()
            pay_passwd = "04A5E788"
            resp = QuanQiuFu().create_card(activation, pay_passwd)
            resp_code = resp.get('resp_code')
            # print(resp_code)
            if resp_code != '0000' and resp_code != '0079':
                resp_msg = resp.get('resp_msg')
                s = '激活卡失败,状态码: ' + resp_code + ',信息: ' + resp_msg + ',激活码为:' + activation
                logging.error(s)
                return jsonify({"code": RET.SERVERERROR, "msg": resp_msg})
            SqlData().update_card_info_field('account_id', user_id, activation)
            card_no = resp.get('response_detail').get('card_no')

            # 如果有免费开卡数量,则每次开卡查询免费数量,没有则不必每次查询
            if free > 0:
                # 查询当次开卡是否免费
                free_num = SqlData().search_user_field('free', user_id)
                # 有免费开卡数量则,设置开卡费用为0元,没有则获取设置的单价
                if free_num > 0:
                    # 设置开卡单价,并更新可免费开卡数量
                    create_price = 0
                    SqlData().update_remove_free(user_id)
                elif free_num == 0:
                    create_price = SqlData().search_user_field('create_price', user_id)

            # 查询账户操作前的账户余额
            before_balance = SqlData().search_user_field('balance', user_id)

            do_money = create_price - create_price * 2
            # 直接更新账户余额,不计算理论余额,用sql更新本次操作费用
            SqlData().update_balance(do_money, user_id)

            balance = SqlData().search_user_field('balance', user_id)

            n_time = xianzai_time()
            SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.CREATE_CARD, 1, card_no, create_price, 0, before_balance,
                                           balance, user_id)

            resp_card_info = QuanQiuFu().query_card_info(card_no)
            # print(resp_card_info)
            if resp_card_info.get('resp_code') != '0000':
                expire_date = ''
                card_verify_code = ''
            else:
                re_de = resp_card_info.get('response_detail')
                expire_date = re_de.get('expire_date')
                card_verify_code = re_de.get('card_verify_code')
            card_name = name_list.pop()
            SqlData().update_card_info(card_no, pay_passwd, n_time, card_name, label, expire_date, card_verify_code, user_id, activation)

            money = str(int(limit) * 100)
            resp = QuanQiuFu().trans_account_recharge(card_no, money)
            resp_code = resp.get('resp_code')
            # print(resp)
            if resp_code == '0000':
                top_money = int(limit)

                # 查询账户操作前的账户余额
                before_balance = SqlData().search_user_field('balance', user_id)

                do_money_top = top_money - top_money * 2
                # 直接更新账户余额,不计算理论余额,用sql更新本次操作费用
                SqlData().update_balance(do_money_top, user_id)

                balance = SqlData().search_user_field('balance', user_id)

                n_time = xianzai_time()
                SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.TOP_UP, 1, card_no, top_money, 0, before_balance, balance, user_id)
            else:
                resp_msg = resp.get('resp_msg')
                s = '充值卡余额失败,状态码: ' + resp_code + ',信息: ' + resp_msg
                logging.error(s)
                card_num = str(i+1)
                s = "成功开卡"+card_num+"张,充值第"+card_num+"失败!请单独充值卡号:"+card_no+"!"
                return jsonify({"code": RET.SERVERERROR, "msg": s})
        return jsonify({"code": RET.OK, "msg": "成功开卡"+str(card_num)+"张!请刷新界面!"})
    except Exception as e:
        logging.error(e)
        results = {"code": RET.SERVERERROR, "msg": MSG.SERVERERROR}
        return jsonify(results)


@user_blueprint.route('/create_card/', methods=['POST'])
@login_required
# @choke_required
def create_card():
    data = json.loads(request.form.get('data'))
    card_name = data.get('card_name')
    top_money = data.get('top_money')
    label = data.get('label')
    user_id = g.user_id
    user_data = SqlData().search_user_index(user_id)
    create_price = user_data.get('create_card')
    min_top = user_data.get('min_top')
    max_top = user_data.get('max_top')
    balance = user_data.get('balance')

    if not check_float(top_money):
        results = {"code": RET.SERVERERROR, "msg": "充值金额不能为小数!"}
        return jsonify(results)

    # 本次开卡需要的费用,计算余额是否充足
    money_all = int(top_money) + create_price
    if money_all > balance:
        results = {"code": RET.SERVERERROR, "msg": "本次消费金额:" + str(money_all) + ",账号余额不足!"}
        return jsonify(results)

    # 计算充值金额是否在允许范围
    if not min_top <= int(top_money) <= max_top:
        results = {"code": RET.SERVERERROR, "msg": "充值金额不在允许范围内!"}
        return jsonify(results)

    try:
        # my_lock.acquire()
        activation = SqlData().search_activation()
        if not activation:
            return jsonify({"code": RET.SERVERERROR, "msg": "请联系服务商添加库存!"})
        pay_passwd = "04A5E788"
        SqlData().update_card_info_field('card_name', 'USING', activation)
        # my_lock.acquire()

        # 开卡及更新相关信息(批量开卡为同一流程步骤)
        resp = QuanQiuFu().create_card(activation, pay_passwd)
        resp_code = resp.get('resp_code')
        if resp_code != '0000' and resp_code != '0079':
            resp_msg = resp.get('resp_msg')
            s = '卡激活失败! 状态码: ' + resp_code + ',信息: ' + resp_msg + '激活码为: ' + activation
            logging.error(s)
            return jsonify({"code": RET.SERVERERROR, "msg": resp_msg})

        SqlData().update_card_info_field('account_id', user_id, activation)
        card_no = resp.get('response_detail').get('card_no')

        # 查询当次开卡是否免费
        free_num = SqlData().search_user_field('free', user_id)
        # 有免费开卡数量则,设置开卡费用为0元,没有则获取设置的单价
        if free_num > 0:
            # 设置开卡单价,并更新可免费开卡数量
            create_price = 0
            SqlData().update_remove_free(user_id)
        elif free_num == 0:
            create_price = SqlData().search_user_field('create_price', user_id)

        # 查询账户操作前的账户余额
        before_balance = SqlData().search_user_field('balance', user_id)

        do_money = create_price - create_price * 2
        # 直接更新账户余额,不计算理论余额,用sql更新本次操作费用
        SqlData().update_balance(do_money, user_id)

        balance = SqlData().search_user_field('balance', user_id)

        n_time = xianzai_time()
        SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.CREATE_CARD, 1, card_no, create_price, 0, before_balance,
                                       balance, user_id)

        # 查询卡信息,及更新相关信息
        resp_card_info = QuanQiuFu().query_card_info(card_no)
        if resp_card_info.get('resp_code') != '0000':
            expire_date = ''
            card_verify_code = ''
        else:
            re_de = resp_card_info.get('response_detail')
            expire_date = re_de.get('expire_date')
            card_verify_code = re_de.get('card_verify_code')
        SqlData().update_card_info(card_no, pay_passwd, n_time, card_name, label, expire_date, card_verify_code, user_id, activation)

        before_balance = SqlData().search_user_field('balance', user_id)
        money = str(int(float(top_money) * 100))

        # 给卡里充值金额,及更新相关信息
        resp = QuanQiuFu().trans_account_recharge(card_no, money)
        resp_code = resp.get('resp_code')
        if resp_code == '0000':
            top_money = float(top_money)
            # 查询账户操作前的账户余额
            before_balance = SqlData().search_user_field('balance', user_id)

            do_money_top = top_money - top_money * 2
            # 直接更新账户余额,不计算理论余额,用sql更新本次操作费用
            SqlData().update_balance(do_money_top, user_id)

            balance = SqlData().search_user_field('balance', user_id)
            n_time = xianzai_time()
            SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.TOP_UP, 1, card_no, top_money, 0, before_balance, balance, user_id)

            return jsonify({"code": RET.OK, "msg": "开卡成功!请刷新界面!"})
        else:
            resp_msg = resp.get('resp_msg')
            s = '充值卡余额失败,状态码: ' + resp_code + ',信息: ' + resp_msg
            logging.error(s)
            return jsonify({"code": RET.SERVERERROR, "msg": "开卡成功,充值失败!"})

    except Exception as e:
        logging.error(e)
        results = {"code": RET.SERVERERROR, "msg": MSG.SERVERERROR}
        return jsonify(results)


@user_blueprint.route('/top_history/', methods=['GET'])
@login_required
def top_history():
    page = request.args.get('page')
    limit = request.args.get('limit')
    user_id = g.user_id
    task_info = SqlData().search_top_history_acc(user_id)
    task_info = sorted(task_info, key=operator.itemgetter('time'))
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    if len(task_info) == 0:
        results['MSG'] = MSG.NODATA
        return jsonify(results)
    page_list = list()
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(task_info)
    return jsonify(results)


@user_blueprint.route('/', methods=['GET'])
@login_required
def account_html():

    '''
    #关闭系统时,返回的信息
    return "<html><div style='position:absolute;z-index:99;padding-top:346px;left:50%;margin-left:-600px;'>" \
           "<h1>{}</h1><div></html>".format('系统临时升级，预计今晚12点前能恢复。做生成的卡可以继续使用。有问题可以联系各自管理员')
    '''

    user_name = g.user_name
    user_id = g.user_id
    dict_info = SqlData().search_user_index(user_id)
    create_card = dict_info.get('create_card')
    # 百分数显示所以乘一百
    refund = dict_info.get('refund') * 100
    min_top = dict_info.get('min_top')
    max_top = dict_info.get('max_top')
    balance = dict_info.get('balance')
    sum_balance = dict_info.get('sum_balance')
    free = dict_info.get('free')

    # 判断账号有效期是否大于30天
    stop_time = dict_info.get('stop_time')
    s = xianzai_time()
    res = verify_login_time(s, stop_time, range_s=2592000)
    if not res:
        stop_string = '到期时间: ' + stop_time
    else:
        stop_string = ''
    out_money = SqlData().search_trans_sum(user_id)
    ex_change = SqlData().search_admin_field('ex_change')
    ex_range = SqlData().search_admin_field('ex_range')
    hand = SqlData().search_admin_field('hand')
    notice = SqlData().search_admin_field('notice')
    pay_money = SqlData().search_card_remain(user_id)

    # 根据推送信息计算失败率
    all_payed = SqlData().search_table_count("push_log WHERE account_id={} AND trans_type!='手续费'".format(user_id))
    fail = SqlData().search_table_count("push_log WHERE account_id={} AND trans_status='交易失败'".format(user_id))
    if all_payed == 0:
        fail_pro = '0.00%'
    else:
        fail_pro = "%.2f%%" % ((fail / all_payed) * 100)
    context = dict()
    context['user_name'] = user_name
    context['balance'] = balance
    context['pay_money'] = pay_money
    context['refund'] = refund
    context['create_card'] = create_card
    context['min_top'] = min_top
    context['max_top'] = max_top
    context['sum_balance'] = sum_balance
    context['out_money'] = out_money
    context['ex_change'] = ex_change
    context['ex_range'] = ex_range
    context['hand'] = hand
    context['notice'] = notice
    context['free'] = free
    context['fail_pro'] = fail_pro
    # print(context)
    context['stop_time'] = stop_string
    return render_template('user/index.html', **context)


@user_blueprint.route('/change_phone', methods=['GET'])
@login_required
def change_phone():
    user_id = g.user_id
    phone_num = request.args.get('phone_num')
    results = dict()
    try:
        SqlData().update_user_field('phone_num', phone_num, user_id)
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        return jsonify(results)
    except Exception as e:
        logging.error(str(e))
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@user_blueprint.route('/one_card_detail', methods=['GET'])
# @login_required
def one_detail():
    try:
        context = dict()
        card_no = request.args.get('card_no')
        resp = QuanQiuFu().query_card_info(card_no)
        if resp.get('resp_code') == '0000':
            detail = resp.get('response_detail')
            freeze_fee_all = detail.get('freeze_fee_all')
            balance = detail.get('balance')
            f_freeze = int(freeze_fee_all)/100
            f_balance = int(balance)/100
            remain = round(f_balance - f_freeze, 2)
            context['balance'] = f_balance
            context['freeze_fee_all'] = f_freeze
            context['remain'] = remain

        resp = QuanQiuFu().auth_trade_query(card_no)
        if resp.get('resp_code') == '0000':
            result_set = resp.get('response_detail').get('result_set')
            info_list = list()
            for i in result_set:
                info_dict = dict()
                info_dict['trade_no'] = i.get('trade_no')
                if i.get('merchant_name') == "香港龙日实业有限公司":
                    info_dict['merchant_name'] = "全球付"
                else:
                    info_dict['merchant_name'] = i.get('merchant_name')
                trans_type = i.get('trans_type')[0:2]
                if trans_type == '01':
                    info_dict['trans_type'] = '充值'
                elif trans_type == '02':
                    info_dict['trans_type'] = '消费'
                else:
                    info_dict['trans_type'] = '暂未定义消费类型'
                status_code = i.get('trans_status')
                info_dict['trans_status'] = TRANS_STATUS.get(status_code)

                info_dict['trans_amount'] = i.get('trans_amount')
                info_dict['trans_currency_type'] = i.get('trans_currency_type')
                # info_dict['trans_local_time'] = i.get('trans_local_time')
                info_dict['trans_local_time'] = i.get('app_time')
                info_dict['auth_settle_amount'] = i.get('auth_settle_amount')
                info_dict['settle_amount'] = i.get('settle_amount')
                info_dict['settle_currency_type'] = i.get('settle_currency_type')
                info_list.append(info_dict)
            context['pay_list'] = info_list
        return render_template('user/card_detail.html', **context)
    except Exception as e:
        logging.error((str(e)))
        return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@user_blueprint.route('/change_detail', methods=['GET'])
@login_required
def change_detail():
    return render_template('user/edit_account.html')


@user_blueprint.route('/change_card_name', methods=['GET', 'POST'])
@login_required
def change_card_name():
    if request.method == 'GET':
        return render_template('user/card_name.html')
    if request.method == 'POST':
        try:
            data = json.loads(request.form.get('data'))
            card_no = data.get('card_no')
            card_name = data.get('card_name')
            card_label = data.get('card_label')
            card_no = card_no.strip()
            if card_name:
                SqlData().update_card_info_card_no('card_name', card_name, card_no)
            if card_label:
                SqlData().update_card_info_card_no('label', card_label, card_no)
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@user_blueprint.route('/card_info', methods=['GET'])
@login_required
def card_info():
    limit = request.args.get('limit')
    page = request.args.get('page')
    card_name = request.args.get('card_name')
    card_num = request.args.get('card_num')
    label = request.args.get('label')
    range_time = request.args.get('range_time')
    results = dict()
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    user_id = g.user_id

    if not card_name and not card_num and not label and not range_time:
        data = SqlData().search_card_info(user_id, '', '', '', '')
        if len(data) == 0:
            results['code'] = RET.SERVERERROR
            results['msg'] = MSG.NODATA
            return jsonify(results)
        data = sorted(data, key=operator.itemgetter('act_time'))
    else:
        name_sql = ''
        if card_name:
            name_sql = "AND card_name LIKE '%" + card_name + "%'"
        card_sql = ''
        if card_num:
            card_sql = "AND card_no LIKE '%" + card_num + "%'"
        label_sql = ''
        if label:
            label_sql = "AND label LIKE '%" + label + "%'"
        time_sql = ''
        if range_time:
            min_time = range_time.split(' - ')[0]
            max_time = range_time.split(' - ')[1] + ' 23:59:59'
            time_sql = "AND act_time BETWEEN " + "'" + min_time + "'" + " and " + "'" + max_time + "'"
        data = SqlData().search_card_info(user_id, name_sql, card_sql, label_sql, time_sql)
        if len(data) == 0:
            results['code'] = RET.SERVERERROR
            results['msg'] = MSG.NODATA
            return jsonify(results)
    page_list = list()
    info = list(reversed(data))
    for i in range(0, len(info), int(limit)):
        page_list.append(info[i:i + int(limit)])
    data = page_list[int(page) - 1]
    data = get_card_remain(data)
    results['data'] = data
    results['count'] = len(info)
    return jsonify(results)


@user_blueprint.route('/edit_user', methods=['GET'])
@login_required
def ch_pass_html():
    return render_template('user/edit_user.html')


@user_blueprint.route('/change_pass', methods=["POST"])
@login_required
def change_pass():
    data = json.loads(request.form.get('data'))
    old_pass = data.get('old_pass')
    new_pass_one = data.get('new_pass_one')
    new_pass_two = data.get('new_pass_two')
    user_id = g.user_id
    pass_word = SqlData().search_user_field('password', user_id)
    results = {'code': RET.OK, 'msg': MSG.OK}
    if not (old_pass == pass_word):
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.PSWDERROR
        return jsonify(results)
    if not (new_pass_one == new_pass_two):
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.PSWDERROR
        return jsonify(results)
    if len(new_pass_one) < 6:
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.PSWDLEN
        return jsonify(results)
    try:
        SqlData().update_user_field('password', new_pass_one, g.user_id)
        return jsonify(results)
    except Exception as e:
        logging.error(e)
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@user_blueprint.route('/user_info', methods=['GET'])
@login_required
def user_info():
    user_name = g.user_name
    user_id = g.user_id
    dict_info = SqlData().search_user_detail(user_id)
    account = dict_info.get('account')
    phone_num = dict_info.get('phone_num')
    balance = dict_info.get('balance')
    context = {
        'user_name': user_name,
        'account': account,
        'balance': balance,
        'phone_num': phone_num,
    }
    return render_template('user/user_info.html', **context)


@user_blueprint.route('/logout', methods=['GET'])
@login_required
def logout():
    session.pop('user_id')
    session.pop('name')
    return redirect('/user/')


@user_blueprint.route('/package/', methods=['GET'])
def package():
    key = request.args.get('key')
    data = SqlData().search_reg_money(key)
    money = data.get('money')
    days = data.get('days')
    price = data.get('price')
    return jsonify({'code': RET.OK, 'money': money, 'days': days, 'price': price})


@user_blueprint.route('/register_pay/', methods=['GET', 'POST'])
def pay_pic():
    if request.method == 'GET':
        u_name = request.args.get('u_name')
        u_acc = request.args.get('u_acc')
        u_pass = request.args.get('u_pass')
        phone = request.args.get('phone')
        middle_key = request.args.get('middle_key')
        package = SqlData().search_reg_package()
        # 取出目前当前收款金额最低的收款码
        qr_info = SqlData().search_qr_code('WHERE status=0')
        if not qr_info:
            url = ''
        else:
            url = ''
            value_list = list()
            for i in qr_info:
                value_list.append(i.get('sum_money'))
            value = min(value_list)
            for n in qr_info:
                money = n.get('sum_money')
                if value == money:
                    url = n.get('qr_code')
                    break

        context = dict()
        context['u_name'] = u_name
        context['u_acc'] = u_acc
        context['u_pass'] = u_pass
        context['phone'] = phone
        context['url'] = url
        context['middle_key'] = middle_key
        context['package_list'] = package
        return render_template('user/register_pay.html', **context)
    if request.method == 'POST':
        '''
        获取充值金额, 保存付款截图. 发送邮件通知管理员
        '''
        try:
            # 两组数据,1,表单信息充值金额,等一下客户信息 2,截图凭证最多可上传5张
            # print(request.form)
            # print(request.files)
            data = json.loads(request.form.get('data'))
            u_name = data.get('u_name')
            u_acc = data.get('u_acc')
            u_pass = data.get('u_pass')
            phone = data.get('phone')
            middle_key = data.get('middle_key')
            url = json.loads(request.form.get('url'))
            package = json.loads(request.form.get('package'))
            results = {'code': RET.OK, 'msg': MSG.OK}

            if not request.files:
                results['code'] = RET.SERVERERROR
                results['msg'] = '请选择支付截图后提交!'
                return jsonify(results)

            data = SqlData().search_reg_money(package)
            reg_money = data.get('money')
            reg_days = data.get('days')

            # 判断是否是用中介的介绍链接进行注册的
            middle_name = ''
            middle_id = 0
            if middle_key:
                try:
                    string = Base64Code().base_decrypt(middle_key.strip())
                    info_list = string.split('_')
                    middle_id = int(info_list[0])
                    middle_name = SqlData().search_middle_field('name', middle_id)
                    account = SqlData().search_middle_field('account', middle_id)
                    if info_list[1] != middle_name or info_list[2] != account:
                        return jsonify({'code': RET.SERVERERROR, 'msg': '请使用正确链接注册!'})
                except Exception as e:
                    logging.error(str(e))
                    return jsonify({'code': RET.SERVERERROR, 'msg': '请使用正确链接注册!'})

            # 保存所有图片
            file_n = 'file_'
            pic_list = list()
            for i in range(5):
                file_name = file_n + str(i+1)
                file_img = request.files.get(file_name)
                if file_img:
                    now_time = sum_code()
                    file_name = u_acc + "_" + now_time + str(i) + ".png"
                    file_path = DIR_PATH.PHOTO_DIR + file_name
                    file_img.save(file_path)
                    pic_list.append(file_name)
            n_time = xianzai_time()
            pic_json = json.dumps(pic_list)
            ver_code = str(uuid.uuid1())[:6]
            context = "客户:  " + u_acc + " , 于" + n_time + "申请注册全球付客户端账号: 金额" + str(reg_money) + "元, 有效使用期为 " + \
                      str(reg_days) + "天。 验证码为: " + ver_code
            stop_time = get_day_after(reg_days)
            SqlData().insert_account_reg(package, n_time, n_time, reg_money, reg_days, stop_time, u_name, u_acc, u_pass, phone, url, middle_id, middle_name, pic_json, ver_code)

            # 获取要推送邮件的邮箱
            top_push = SqlData().search_admin_field('top_push')
            top_dict = json.loads(top_push)
            email_list = list()
            for i in top_dict:
                email_list.append(top_dict.get(i))
            for p in email_list:
                send(context, pic_list, p)

            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@user_blueprint.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        middle_key = request.args.get('middle_key')
        if middle_key:
            try:
                string = Base64Code().base_decrypt(middle_key.strip())
                #  验证解密后的参数是否是符合要求(id_用户名_账号)
                info_list = string.split('_')
                middle_id = info_list[0]
                name = SqlData().search_middle_field('name', middle_id)
                account = SqlData().search_middle_field('account', middle_id)
                if info_list[1] != name or info_list[2] != account:
                    return  "<html><div style='position:absolute;z-index:99;padding-top:346px;left:50%;margin-left:-600px;'>" \
                            "<h1>{}</h1><div></html>".format('链接残缺请使用正确的介绍链接注册!!')

            except:
                return "<html><div style='position:absolute;z-index:99;padding-top:346px;left:50%;margin-left:-600px;'>" \
                       "<h1>{}</h1><div></html>".format('链接残缺请使用正确的介绍链接注册!')

        # 给界面设置一个使用cache的key,设置唯一的key核对验证码
        ver_key = verify_code(18)
        context = dict()
        context['ver_key'] = ver_key
        context['middle_key'] = middle_key if middle_key else ''
        return render_template('user/register.html', **context)
    if request.method == 'POST':
        try:
            data = json.loads(request.form.get('data'))
            u_name = data.get('u_name')
            u_acc = data.get('u_acc')
            u_pass = data.get('u_pass')
            phone = data.get('phone')
            ver_code = data.get('ver_code')
            ver_key = data.get('ver_key')
            # 取出缓存中验证码
            server_code = cache.get(ver_key)
            # server_code = '111'

            # 以下是对注册参数的校验
            if not all([u_name, u_pass, phone, ver_code, ver_key]):
                return jsonify({'code': RET.SERVERERROR, 'msg': '请补全信息后提交!'})
            chinese = is_chinese(u_acc)
            if chinese:
                return jsonify({'code': RET.SERVERERROR, 'msg': '账号中包含中文!'})
            # 检验用户名和账号是否存在
            res1 = SqlData().search_user_field_name('id', u_name)
            # 每天用户名默认电话,所以没有用户名就检验电话
            if not u_acc:
                u_acc = phone
            res2 = SqlData().search_user_info(u_acc)
            if res1 or res2:
                return jsonify({'code': RET.SERVERERROR, 'msg': '用户名或账号已存在!'})
            if not 6 <= len(u_pass) <= 12:
                return jsonify({'code': RET.SERVERERROR, 'msg': '密码长度不符合要求!'})
            if 8 < len(u_name):
                return jsonify({'code': RET.SERVERERROR, 'msg': '用户名过长!'})
            if 18 < len(u_acc):
                return jsonify({'code': RET.SERVERERROR, 'msg': '账号长度过长!'})
            if server_code is None:
                return jsonify({'code': RET.SERVERERROR, 'msg': '验证码过期!请重新获取!'})
            if ver_code != server_code:
                return jsonify({'code': RET.SERVERERROR, 'msg': '验证码错误请刷新后重试!'})
            else:
                return jsonify({'code': RET.OK, 'msg': MSG.OK})
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@user_blueprint.route('/ver_code/', methods=['POST'])
def ver_code_send():
    if request.method == 'POST':
        data = json.loads(request.form.get('data'))
        phone = data.get('phone')
        ver_key = data.get('ver_key')

        _code = verify_code(6, False)
        res = CCP().send_Template_sms(phone, [_code, '60s'], 488547,)
        if res == 0:
            cache.set(ver_key, _code, timeout=120)
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '短信发送失败!请检查号码是否正确!'})


@user_blueprint.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        context = dict()
        # 判断是否是通过中介链接过来的,是则保留middle_key
        referer = request.headers.get('Referer')
        if referer:
            results = re.findall('middle_key=(.*)', referer)
            if results:
                context['middle_key'] = '?middle_key=' + results[0]

        return render_template('user/login.html', **context)

    if request.method == 'POST':
        user_name = request.form.get('uname')
        user_pass = request.form.get('upwd')
        if not all([user_name, user_pass]):
            return jsonify({'code': RET.SERVERERROR, 'msg': '请完善登录信息后重试!'})
        results = {'code': RET.OK, 'msg': MSG.OK}
        user_data = SqlData().search_user_info(user_name)
        try:
            if user_data:
                user_id = user_data.get('user_id')
                pass_word = user_data.get('password')
                name = user_data.get('name')
                stop_time = user_data.get('stop_time')
                n_time = xianzai_time()
                if not verify_login_time(n_time, stop_time):
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '账号已到期,请联系管理员处理!'
                    return jsonify(results)
                if user_pass == pass_word:
                    session['user_id'] = user_id
                    session['name'] = name
                    return jsonify(results)
                else:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '账号密码错误!'
                    return jsonify(results)
            else:
                results['code'] = RET.SERVERERROR
                results['msg'] = '账号密码错误!'
                return jsonify(results)

        except Exception as e:
            logging.error(str(e))
            results['code'] = RET.SERVERERROR
            results['msg'] = '账号密码错误!'
            return jsonify(results)
