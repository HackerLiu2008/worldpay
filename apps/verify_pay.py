import base64
import json
import logging
from flask import render_template, request, jsonify, session
from tools_me.mysql_tools import SqlData
from tools_me.other_tools import sum_code, xianzai_time, verify_required
from tools_me.parameter import RET, MSG, DIR_PATH
from tools_me.send_sms.send_sms import CCP
from . import verify_pay_blueprint


@verify_pay_blueprint.route('/login/', methods=['GET', 'POST'])
def verify_login():
    if request.method == 'GET':
        return render_template('verify_pay/login.html')
    if request.method == 'POST':
        data = request.values.to_dict()
        user_name = data.get('username')
        pass_word = data.get('password')
        if user_name == "GUTE123" and pass_word == "think988&":
            session['verify_pay'] = 'T'
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '账号或密码错误!'})


@verify_pay_blueprint.route('/')
@verify_required
def verify_index():
    return render_template('verify_pay/index.html')


@verify_pay_blueprint.route('/pay_log/', methods=['GET'])
@verify_required
def pay_log():
    results = dict()
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    limit = request.args.get('limit')
    page = request.args.get('page')
    status = request.args.get('status')
    time_range = request.args.get('time_range')
    if time_range:
        start_time = "'" + time_range.split(' - ')[0] + "'"
        end_time = "'" + time_range.split(' - ')[1] + " 23:59:59'"
        sql = "AND ver_time BETWEEN " + start_time + " AND " + end_time
    else:
        sql = ''
    data = SqlData().search_pay_log(status, sql_time=sql)
    if not data:
        results['msg'] = MSG.NODATA
        return jsonify(results)
    info = list(reversed(data))
    if time_range:
        info_list = info
    else:
        page_list = list()
        for i in range(0, len(info), int(limit)):
            page_list.append(info[i:i + int(limit)])
        info_list = page_list[int(page) - 1]

    # 查询当次充值时的账号总充值金额
    new_list = list()
    for o in info_list:
        x_time = o.get('ver_time')
        user_id = o.get('cus_id')
        sum_money = SqlData().search_time_sum_money(x_time, user_id)
        o['sum_balance'] = round(sum_money, 2)
        new_list.append(o)

    results['data'] = new_list
    results['count'] = len(data)
    return jsonify(results)


@verify_pay_blueprint.route('/top_up/', methods=['GET', 'POST'])
@verify_required
def top_up():
    if request.method == 'GET':
        pay_time = request.args.get('pay_time')
        cus_name = request.args.get('cus_name')
        context = dict()
        context['pay_time'] = pay_time
        context['cus_name'] = cus_name
        return render_template('verify_pay/check.html', **context)
    if request.method == 'POST':
        try:
            results = dict()
            data = json.loads(request.form.get('data'))
            pay_time = data.get('pay_time')
            cus_name = data.get('cus_name')
            check = data.get('check')
            ver_code = data.get('ver_code')
            money = data.get('money')

            # 校验参数验证激活码
            if check != 'yes':
                results['code'] = RET.SERVERERROR
                results['msg'] = '请确认已收款!'
                return jsonify(results)
            pass_wd = SqlData().search_pay_code('ver_code', cus_name, pay_time)
            if pass_wd != ver_code:
                results['code'] = RET.SERVERERROR
                results['msg'] = '验证码错误!'
                return jsonify(results)

            status = SqlData().search_pay_code('status', cus_name, pay_time)
            if status != '待充值':
                results['code'] = RET.SERVERERROR
                results['msg'] = '该订单已充值,请刷新界面!'
                return jsonify(results)

            # 验证成功后,做客户账户充值
            cus_id = SqlData().search_user_field_name('id', cus_name)

            # 判断是否需要根据输入的美元金额扣除手续费在充值
            if money:
                money = float(money)
                # 更新新的充值金额
                dollar_hand = SqlData().search_admin_field('dollar_hand')
                money = round(money / (1+dollar_hand), 2)
                SqlData().update_pay_money(money, cus_id, pay_time)

            money = SqlData().search_pay_code('top_money', cus_name, pay_time)
            pay_num = sum_code()
            t = xianzai_time()
            before = SqlData().search_user_field_name('balance', cus_name)

            user_id = SqlData().search_user_field_name('id', cus_name)

            # 更新首款码收款金额
            pay_money = SqlData().search_pay_code('pay_money', cus_name, pay_time)
            url = SqlData().search_pay_code('url', cus_name, pay_time)
            SqlData().update_qr_money('top_money', pay_money, url)

            # 更新账户余额
            SqlData().update_user_balance(money, user_id)

            # 实时查询当前余额不以理论计算为结果
            balance = SqlData().search_user_field('balance', user_id)

            # 更新客户充值记录
            SqlData().insert_top_up(pay_num, t, money, before, balance, user_id, '系统')

            # 更新pay_log的订单的充值状态
            SqlData().update_pay_status('已充值', t, cus_id, pay_time)

            phone = SqlData().search_user_field_name('phone_num', cus_name)
            mid_phone = SqlData().search_pay_code('phone', cus_name, pay_time)

            # 给客户和代充值人发送短信通知
            if phone:
                CCP().send_Template_sms(phone, [cus_name, t, money], 478898)
            if mid_phone:
                CCP().send_Template_sms(mid_phone, [cus_name, t, money], 478898)
            results['code'] = RET.OK
            results['msg'] = MSG.OK
            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            results = dict()
            results['code'] = RET.SERVERERROR
            results['msg'] = MSG.SERVERERROR
            return jsonify(results)


@verify_pay_blueprint.route('/del_pay/', methods=['POST'])
@verify_required
def del_pay():
    try:
        data = json.loads(request.form.get('data'))
        user_name = data.get('user_name')
        pay_time = data.get('pay_time')
        user_id = SqlData().search_user_field_name('id', user_name)
        SqlData().del_pay_log(user_id, pay_time)
        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        return jsonify(results)
    except Exception as e:
        logging.error(str(e))
        results = dict()
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@verify_pay_blueprint.route('/photo_base/', methods=['GET'])
@verify_required
def photo_base():
    try:
        pic_json = request.args.get('file_name')
        pic_list = json.loads(pic_json)
        if pic_list == [] or pic_list is None:
            return jsonify({'code': RET.SERVERERROR, 'msg': '该订单没有支付截图!'})
        _html = "<!DOCTYPE html><html><head><title>支付截图</title></head><body>{}</body></html>"
        img_all = ""
        for i in pic_list:
            photo_path = DIR_PATH.PHOTO_DIR + i
            with open(photo_path, 'rb') as f:
                base64_data = base64.b64encode(f.read())
                s = bytes.decode(base64_data)
                img = '<img src="data:image/png;base64,{}" height="1200" width="600">'.format(s)
                img_all += img
        html_all = _html.format(img_all)
        return jsonify({'code': RET.OK, 'data': html_all})
    except Exception as e:
        logging.error(str(e))
        return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@verify_pay_blueprint.route('/account_reg/', methods=['GET'])
@verify_required
def account_reg():
    results = dict()
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    limit = request.args.get('limit')
    page = request.args.get('page')
    status = request.args.get('status')
    time_range = request.args.get('time_range')
    if time_range:
        start_time = "'" + time_range.split(' - ')[0] + "'"
        end_time = "'" + time_range.split(' - ')[1] + " 23:59:59'"
        sql = "AND ver_time BETWEEN " + start_time + " AND " + end_time
    else:
        sql = ''
    data = SqlData().search_account_reg(status, sql_line=sql)
    if not data:
        results['msg'] = MSG.NODATA
        return jsonify(results)
    info = list(reversed(data))
    if time_range:
        info_list = info
    else:
        page_list = list()
        for i in range(0, len(info), int(limit)):
            page_list.append(info[i:i + int(limit)])
        info_list = page_list[int(page) - 1]

    results['data'] = info_list
    results['count'] = len(data)
    return jsonify(results)


@verify_pay_blueprint.route('/reg_check/', methods=['GET', 'POST'])
@verify_required
def reg_check():
    if request.method == 'GET':
        pay_time = request.args.get('pay_time')
        u_name = request.args.get('u_name')
        package = request.args.get('package')
        context = dict()
        context['pay_time'] = pay_time
        context['u_name'] = u_name
        context['package'] = package
        return render_template('verify_pay/reg_check.html', **context)
    if request.method == 'POST':
        try:
            results = dict()
            data = json.loads(request.form.get('data'))
            pay_time = data.get('pay_time')
            u_name = data.get('u_name')
            package = data.get('package')
            check = data.get('check')
            ver_code = data.get('ver_code')

            # 校验参数验证激活码
            if check != 'yes':
                results['code'] = RET.SERVERERROR
                results['msg'] = '请确认已收款!'
                return jsonify(results)

            # 查询邮件中的验证码
            pass_wd = SqlData().search_account_reg_field('ver_code', pay_time, u_name)
            if pass_wd != ver_code:
                results['code'] = RET.SERVERERROR
                results['msg'] = '验证码错误!'
                return jsonify(results)

            # 却认订单状态
            status = SqlData().search_account_reg_field('status', pay_time, u_name)
            if status:
                results['code'] = RET.SERVERERROR
                results['msg'] = '该订单已充值,请刷新界面!'
                return jsonify(results)

            # 验证成功后,做新增客户端账号(基础参数还需:建卡费, 最低充值,最高充值)
            # 根据选择的套餐查出对应的收费标准
            data = SqlData().search_reg_money(package)
            price = data.get('price')
            refund = data.get('refund')
            min_top = data.get('min_top')
            max_top = data.get('max_top')
            u_acc = SqlData().search_account_reg_field('u_acc', pay_time, u_name)
            u_pass = SqlData().search_account_reg_field('u_pass', pay_time, u_name)
            phone = SqlData().search_account_reg_field('phone', pay_time, u_name)
            start_time = SqlData().search_account_reg_field('start_time', pay_time, u_name)
            stop_time = SqlData().search_account_reg_field('stop_time', pay_time, u_name)
            SqlData().insert_account(u_acc, u_pass, phone, u_name, price, refund, min_top, max_top, start_time, stop_time)

            # 添加默认充值记录0元(用于单独充值结算总充值金额避免BUG)
            n_time = xianzai_time()
            account_id = SqlData().search_user_field_name('id', u_name)
            SqlData().insert_top_up('10001', n_time, 0, 0, 0, account_id, '系统')

            # 判断是否是中介介绍,如果是则绑定到中介
            middle_id = SqlData().search_account_reg_field('middle_id', pay_time, u_name)
            if middle_id:
                SqlData().update_user_field_int('middle_id', middle_id, account_id)

            # 更新首款码收款金额
            pay_money = SqlData().search_account_reg_field('reg_money', pay_time, u_name)
            url = SqlData().search_account_reg_field('url', pay_time, u_name)
            SqlData().update_qr_money('top_money', pay_money, url)

            # 更新订单状态和确认时间
            SqlData().update_account_reg_field('status', '已确认', pay_time, u_name)
            SqlData().update_account_reg_field('ver_time', n_time, pay_time, u_name)

            # 给客户和代充值人发送短信通知
            if phone:
                CCP().send_Template_sms(phone, [u_name, n_time, u_acc, u_pass], 488712)
            results['code'] = RET.OK
            results['msg'] = MSG.OK
            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            results = dict()
            results['code'] = RET.SERVERERROR
            results['msg'] = MSG.SERVERERROR
            return jsonify(results)
