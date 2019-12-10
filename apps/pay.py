import logging
import re
import uuid
from flask import render_template, request, json, jsonify, session
from tools_me.mysql_tools import SqlData
from tools_me.other_tools import time_str, xianzai_time, pay_required, sum_code
from tools_me.parameter import RET, MSG, DIR_PATH
from tools_me.send_email import send
from . import pay_blueprint


@pay_blueprint.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('pay/login.html')
    if request.method == 'POST':
        data = json.loads(request.form.get('data'))
        login = data.get('login')
        pwd = data.get('pwd')
        code = data.get('code')
        ver_code = data.get('ver_code')
        if ver_code != code:
            return jsonify({'code': RET.SERVERERROR, 'msg': '验证码错误!区分大小写!'})
        elif login == 'quanqiufu!' and pwd == 'trybest@':
            session['pay_login'] = 'T'
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '账号或密码错误!'})


@pay_blueprint.route('/', methods=['GET'])
@pay_required
def index_pay():
    ex_change = SqlData().search_admin_field('ex_change')
    ex_range = SqlData().search_admin_field('ex_range')
    hand = SqlData().search_admin_field('hand')
    dollar_hand = SqlData().search_admin_field('dollar_hand')
    context = dict()
    context['ex_change'] = ex_change
    context['ex_range'] = ex_range
    context['hand'] = hand
    context['dollar_hand'] = dollar_hand
    return render_template('pay/index.html', **context)


@pay_blueprint.route('/acc_top_cn/', methods=['POST'])
@pay_required
def top_cn():
    if request.method == 'POST':
        '''
        1:校验前端数据是否正确
        2:查看实时汇率有没有变动
        3:核实客户是否存在
        '''
        try:
            data = json.loads(request.form.get('data'))
            sum_money = data.get('sum_money')
            top_money = data.get('top_money')
            cus_name = data.get('cus_name')
            cus_account = data.get('cus_account')
            phone = data.get('phone')
            res = SqlData().search_user_check(cus_name, cus_account)
            if not res:
                return jsonify({'code': RET.SERVERERROR, 'msg': '没有该用户!请核实后重试!'})
            if phone:
                ret = re.match(r"^1[35789]\d{9}$", phone)
                if not ret:
                    results = dict()
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '请输入符合规范的电话号码!'
                    return jsonify(results)
            ex_change = SqlData().search_admin_field('ex_change')
            ex_range = SqlData().search_admin_field('ex_range')
            hand = SqlData().search_admin_field('hand')
            _money_self = float(top_money) * (ex_change + ex_range) * (hand + 1)
            money_self = round(_money_self, 10)
            sum_money = round(float(sum_money), 10)
            if money_self == sum_money:
                return jsonify({'code': RET.OK, 'msg': MSG.OK})
            else:
                return jsonify({'code': RET.SERVERERROR, 'msg': '汇率已变动!请刷新界面后重试!'})
        except Exception as e:
            ip = request.headers.get('Host')
            s = '请求IP是: ' + str(ip)
            logging.error(s)
            return jsonify({'code': RET.SERVERERROR, 'msg': '别玩了!都被你玩坏了!'})


@pay_blueprint.route('/acc_top_dollar/', methods=['POST'])
@pay_required
def top_dollar():
    if request.method == 'POST':
        '''
        1:校验前端数据是否正确
        2:查看实时汇率有没有变动
        3:核实客户是否存在
        '''
        data = json.loads(request.form.get('data'))
        sum_money = data.get('sum_money')
        top_money = data.get('top_money')
        cus_name = data.get('cus_name')
        cus_account = data.get('cus_account')
        phone = data.get('phone')
        res = SqlData().search_user_check(cus_name, cus_account)
        if not res:
            return jsonify({'code': RET.SERVERERROR, 'msg': '没有该用户!请核实后重试!'})
        if phone:
            ret = re.match(r"^1[35789]\d{9}$", phone)
            if not ret:
                results = dict()
                results['code'] = RET.SERVERERROR
                results['msg'] = '请输入符合规范的电话号码!'
                return jsonify(results)
        dollar = SqlData().search_admin_field('dollar_hand')
        _money_self = float(top_money) * (dollar + 1)
        money_self = round(_money_self, 10)
        sum_money = round(float(sum_money), 10)
        if money_self == sum_money:
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '手续费已变动!请刷新界面后重试!'})


@pay_blueprint.route('/pay_pic/', methods=['GET', 'POST'])
@pay_required
def pay_pic():
    if request.method == 'GET':
        sum_money = request.args.get('sum_money')
        top_money = request.args.get('top_money')
        cus_name = request.args.get('cus_name')
        cus_account = request.args.get('cus_account')
        phone = request.args.get('phone')
        ex_change = request.args.get('ex_change')
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
        context['sum_money'] = sum_money
        context['top_money'] = top_money
        context['cus_name'] = cus_name
        context['cus_account'] = cus_account
        context['phone'] = phone
        context['url'] = url
        context['ex_change'] = ex_change
        return render_template('pay/pay_pic.html', **context)
    if request.method == 'POST':
        '''
        获取充值金额, 保存付款截图. 发送邮件通知管理员
        '''
        try:
            # 两组数据,1,表单信息充值金额,等一下客户信息 2,截图凭证最多可上传5张
            # print(request.form)
            # print(request.files)
            data = json.loads(request.form.get('data'))
            top_money = data.get('top_money')
            sum_money = data.get('sum_money')
            cus_name = data.get('cus_name')
            cus_account = data.get('cus_account')
            phone = data.get('phone')
            exchange = data.get('exchange')
            url = json.loads(request.form.get('url'))
            results = {'code': RET.OK, 'msg': MSG.OK}
            # 保存所有图片
            file_n = 'file_'
            pic_list = list()
            for i in range(5):
                file_name = file_n + str(i+1)
                file_img = request.files.get(file_name)
                if file_img:
                    now_time = sum_code()
                    file_name = cus_account + "_" + now_time + str(i) + ".png"
                    file_path = DIR_PATH.PHOTO_DIR + file_name
                    file_img.save(file_path)
                    pic_list.append(file_name)
            n_time = xianzai_time()
            vir_code = str(uuid.uuid1())[:6]
            ex_range = SqlData().search_admin_field('ex_range')
            hand = SqlData().search_admin_field('hand')
            if exchange != 'None':
                top_exchange = round((float(exchange) + ex_range) * (hand + 1), 5)
                top_exchange_str = ' 充值汇率为: ' + str(top_exchange) + ", "
                money_type = '人民币'
            else:
                money_type = '美元'
                top_exchange_str = ''
            context = "客户:  " + cus_name + " , 于" + n_time + "在线申请充值: " + top_money + "美元, 折和" + money_type + ": " + \
                      sum_money + "元。本次计算汇率为: " + exchange + "," + top_exchange_str + " 验证码为: " + vir_code

            cus_id = SqlData().search_user_check(cus_name, cus_account)
            sum_money = float(sum_money)
            top_money = float(top_money)
            pic_json = json.dumps(pic_list)
            SqlData().insert_pay_log(n_time, sum_money, top_money, vir_code, '待充值', phone, url, pic_json, cus_id)

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
