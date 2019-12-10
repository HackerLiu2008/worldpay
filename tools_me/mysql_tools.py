import pymysql
import logging


class SqlData(object):
    def __init__(self):
        host = "114.116.236.27"
        port = 3306
        user = "root"
        password = "gute123"
        # password = "admin"
        database = "world_pay"
        self.connect = pymysql.Connect(
            host=host, port=port, user=user,
            passwd=password, db=database,
            charset='utf8'
        )
        self.cursor = self.connect.cursor()

    def close_connect(self):
        if self.cursor:
            self.cursor.close()
        if self.connect:
            self.connect.close()

    # 一下是用户方法-----------------------------------------------------------------------------------------------------

    # 登录查询
    def search_user_info(self, account):
        sql = "SELECT id, password, name, start_time, stop_time FROM account WHERE BINARY account = '{}'".format(account)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        else:
            user_data = dict()
            user_data['user_id'] = rows[0][0]
            user_data['password'] = rows[0][1]
            user_data['name'] = rows[0][2]
            user_data['start_time'] = str(rows[0][3])
            user_data['stop_time'] = str(rows[0][4])
            return user_data

    # 查询用户首页数据信息
    def search_user_index(self, user_id):
        sql = "SELECT create_price, refund, min_top, max_top, balance, sum_balance, free, stop_time FROM account WHERE id = {}".format(
            user_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        user_info = dict()
        user_info['create_card'] = rows[0][0]
        user_info['refund'] = rows[0][1]
        user_info['min_top'] = rows[0][2]
        user_info['max_top'] = rows[0][3]
        user_info['balance'] = rows[0][4]
        user_info['sum_balance'] = rows[0][5]
        user_info['free'] = rows[0][6]
        user_info['stop_time'] = str(rows[0][7])
        return user_info

    # 用户基本信息资料
    def search_user_detail(self, user_id):
        sql = "SELECT account, phone_num, balance FROM account WHERE id = {}".format(user_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        user_info = dict()
        user_info['account'] = rows[0][0]
        user_info['phone_num'] = rows[0][1]
        user_info['balance'] = rows[0][2]
        return user_info

    # 查询用户的某一个字段信息
    def search_user_field(self, field, user_id):
        sql = "SELECT {} FROM account WHERE id = {}".format(field, user_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    # 更新用户的某一个字段信息(str)
    def update_user_field(self, field, value, user_id):
        sql = "UPDATE account SET {} = '{}' WHERE id = {}".format(field, value, user_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新用户字段" + field + "失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_user_field_int(self, field, value, user_id):
        sql = "UPDATE account SET {} = {} WHERE id = {}".format(field, value, user_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新用户字段" + field + "失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_user_bala(self, field, value, user_id):
        sql = "UPDATE account SET {} = {} WHERE id = {}".format(field, value, user_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新用户字段" + field + "失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_top_history_acc(self, user_id):
        sql = "SELECT * FROM top_up WHERE account_id={}".format(user_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        else:
            for i in rows:
                info_dict = dict()
                info_dict['pay_num'] = i[1]
                info_dict['time'] = str(i[2])
                info_dict['money'] = i[3]
                info_dict['before_balance'] = i[4]
                info_dict['balance'] = i[5]
                info_dict['trans_type'] = i[7]
                info_list.append(info_dict)
            return info_list

    def search_activation(self):
        # sql = "SELECT activation from card_info WHERE card_no is null AND card_name = '' AND account_id is null LIMIT 1"
        sql = "select activation from card_info  where card_no is null AND card_name = '' AND account_id is null order by rand() limit 1"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        return rows[0][0]

    def search_activation_count(self):
        sql = "SELECT COUNT(activation) from card_info WHERE card_no is null AND account_id is null AND card_name = ''"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        return rows[0][0]

    def update_card_info_field(self, field, value, activation):
        sql = "UPDATE card_info SET {}='{}' WHERE activation='{}'".format(field, value, activation)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新卡信息失败!")
            self.connect.rollback()
        self.close_connect()

    def update_card_info_card_no(self, field, value, card_no):
        sql = "UPDATE card_info SET {}='{}' WHERE card_no='{}'".format(field, value, card_no)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新卡信息失败!")
            self.connect.rollback()
        self.close_connect()

    def update_card_remain(self, field, value, card_no):
        sql = "UPDATE card_info SET {}={} WHERE card_no='{}'".format(field, value, card_no)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新卡信息失败!")
            self.connect.rollback()
        self.close_connect()

    def search_card_field(self, field, crad_no):
        sql = "SELECT {} from card_info WHERE card_no='{}'".format(field, crad_no)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        return rows[0][0]

    def search_user_check(self, name, account):
        sql = "SELECT id FROM account WHERE name='{}' AND account='{}'".format(name, account)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        return rows[0][0]

    def update_card_info(self, card_no, pay_passwd, act_time, card_name, label, expire, cvv, account_id, activation):
        sql = "UPDATE card_info SET card_no = '{}', pay_passwd='{}', act_time='{}', card_name='{}', label='{}', expire = '{}'," \
              " cvv = '{}', account_id = {} WHERE activation = '{}'".format(card_no, pay_passwd, act_time, card_name,
                                                                            label,
                                                                            expire, cvv, account_id, activation)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新卡信息失败!")
            self.connect.rollback()
        self.close_connect()

    def search_card_info(self, user_id, name_sql, card_sql, label, time_sql):
        sql = "SELECT * FROM card_info WHERE account_id={} {} {} {} {}".format(user_id, name_sql, card_sql, label,
                                                                               time_sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        else:
            for i in rows:
                info_dict = dict()
                info_dict['card_no'] = "\t" + i[2]
                info_dict['act_time'] = str(i[4])
                info_dict['card_name'] = i[5]
                info_dict['label'] = i[6]
                expire = i[7]
                if expire:
                    info_dict['expire'] = "\t" + expire[4:6] + "/" + expire[2:4]
                else:
                    info_dict['expire'] = ""
                cvv = i[8]
                if cvv:
                    info_dict['cvv'] = "\t" + cvv
                else:
                    info_dict['cvv'] = ""
                info_list.append(info_dict)
            return info_list

    def insert_account_trans(self, date, trans_type, do_type, num, card_no, do_money, hand_money, before_balance,
                             balance, account_id):
        sql = "INSERT INTO account_trans(do_date, trans_type, do_type, num, card_no, do_money, hand_money, before_balance," \
              " balance, account_id) VALUES('{}','{}','{}',{},'{}',{},{},{},{},{})".format(date, trans_type, do_type,
                                                                                           num, card_no, do_money,
                                                                                           hand_money, before_balance,
                                                                                           balance, account_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加用户交易记录失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_account_trans(self, account_id, card_sql, time_sql):
        sql = "SELECT * FROM account_trans WHERE account_id = {} {} {}".format(account_id, card_sql, time_sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        for i in rows:
            info_dict = dict()
            info_dict['u_id'] = i[0]
            info_dict['date'] = str(i[1])
            info_dict['trans_type'] = i[2]
            info_dict['do_type'] = i[3]
            info_dict['num'] = i[4]
            info_dict['card_no'] = "\t" + i[5]
            info_dict['do_money'] = i[6]
            info_dict['hand_money'] = i[7]
            info_dict['before_balance'] = i[8]
            info_dict['balance'] = i[9]
            info_list.append(info_dict)
        return info_list

    def search_trans_sum(self, account_id):
        # 2019-11-01 20:50:00 更该计费方式,退款不增加总充值金额,只变动账号余额和以消费金额,所以要按两个条件段搜索
        sql = "SELECT SUM(do_money) FROM account_trans WHERE account_id={} ".format(account_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows[0][0]:
            return 0
        sum_money = round(rows[0][0], 2)
        return sum_money

    # 一下是中介使用方法-------------------------------------------------------------------------------------------------

    # 查询中介登录信息

    def search_middle_login(self, account):
        sql = "SELECT id, password FROM middle WHERE BINARY account='{}'".format(account)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows

    # 查询中介的你某一个字段信息
    def search_middle_field(self, field, middle_id):
        sql = "SELECT {} FROM middle WHERE id={}".format(field, middle_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

        # 用户基本信息资料

    def search_middle_detail(self, middle_id):
        sql = "SELECT account, phone_num, card_price FROM middle WHERE id = {}".format(middle_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        user_info = dict()
        user_info['account'] = rows[0][0]
        user_info['phone_num'] = rows[0][1]
        user_info['card_price'] = rows[0][2]
        return user_info

    # 更新用户的某一个字段信息(str)
    def update_middle_field(self, field, value, middle_id):
        sql = "UPDATE middle SET {} = '{}' WHERE id = {}".format(field, value, middle_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新中介字段" + field + "失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_user_field_middle(self, middle_id):
        sql = "SELECT id, name FROM account WHERE middle_id = {}".format(middle_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        account_list = list()
        if not rows:
            return account_list
        for i in rows:
            info_dict = dict()
            info_dict['id'] = i[0]
            info_dict['name'] = i[1]
            account_list.append(info_dict)
        return account_list

    def search_user_middle_info(self, middle_id):
        sql = "SELECT id, name, sum_balance, balance FROM account WHERE middle_id = {}".format(middle_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        account_list = list()
        if not rows:
            return account_list
        for i in rows:
            info_dict = dict()
            info_dict['id'] = i[0]
            info_dict['name'] = i[1]
            info_dict['sum_balance'] = i[2]
            info_dict['balance'] = i[3]
            account_list.append(info_dict)
        return account_list

    def search_card_count(self, account_id, time_range):
        sql = "SELECT COUNT(*) FROM card_info WHERE account_id={} {}".format(account_id, time_range)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    def search_card_count_of_money(self, u_id, time_range):
        sql = "SELECT COUNT(*) FROM card_info LEFT JOIN account_trans ON card_info.card_no=account_trans.card_no WHERE " \
              "card_info.account_id={} AND account_trans.do_type='开卡' AND account_trans.do_money != 0 {}".format(u_id,
                                                                                                                 time_range)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return 0
        return rows[0][0]

    def search_card_remain(self, user_id):
        sql = "SELECT SUM(remain) FROM card_info WHERE account_id={}".format(user_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return 0
        return rows[0][0]

    def insert_middle_money(self, middle_id, start_time, end_time, card_num, create_price, sum_money, create_time,
                            pay_status, detail):
        sql = "INSERT INTO middle_money(middle_id, start_time, end_time, card_num, create_price, sum_money," \
              " create_time, pay_status, detail) VALUES ({},'{}','{}',{},{},{},'{}','{}','{}')".format(
            middle_id, start_time, end_time, card_num, create_price, sum_money, create_time, pay_status, detail)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("插入中介开卡费记录失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_middle_money(self, middle_id):
        sql = "SELECT * FROM middle_money WHERE middle_id={}".format(middle_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        for i in rows:
            info_dict = dict()
            info_dict['id'] = i[0]
            info_dict['start_time'] = str(i[2])
            info_dict['end_time'] = str(i[3])
            info_dict['card_num'] = i[4]
            info_dict['create_price'] = i[5]
            info_dict['sum_money'] = i[6]
            info_dict['create_time'] = str(i[7])
            info_dict['pay_status'] = i[8]
            if i[9]:
                info_dict['pay_time'] = str(i[9])
            else:
                info_dict['pay_time'] = ""
            info_list.append(info_dict)
        return info_list

    def search_middle_money_field(self, field, info_id):
        sql = "SELECT {} FROM middle_money WHERE id={}".format(field, info_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    # 以下是终端使用接口-------------------------------------------------------------------------------------------------

    # 验证登录
    def search_admin_login(self, account, password):
        sql = "SELECT id, name FROM admin WHERE BINARY account='{}' AND BINARY password='{}'".format(account, password)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0], rows[0][1]

    def search_account_info(self, info):
        sql = "SELECT * FROM account {}".format(info)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        account_list = list()
        if not rows:
            return account_list
        else:
            for i in rows:
                account_dict = dict()
                account_dict['u_id'] = i[0]
                account_dict['account'] = i[1]
                account_dict['password'] = i[2]
                account_dict['name'] = i[4]
                account_dict['create_price'] = i[5]
                account_dict['refund'] = i[6]
                account_dict['min_top'] = i[7]
                account_dict['max_top'] = i[8]
                account_dict['balance'] = i[9]
                account_dict['sum_balance'] = i[10]
                account_dict['free'] = i[12]
                account_list.append(account_dict)
            return account_list

    def update_account_field(self, field, value, name):
        sql = "UPDATE account SET {}={} WHERE name='{}'".format(field, value, name)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新用户字段" + field + "失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_account_field_str(self, field, value, name):
        sql = "UPDATE account SET {}='{}' WHERE name='{}'".format(field, value, name)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新用户字段" + field + "失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_user_field_name(self, field, name):
        sql = "SELECT {} FROM account WHERE name = '{}'".format(field, name)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        return rows[0][0]

    def update_user_balance(self, money, id):
        sql = "UPDATE account set sum_balance=sum_balance+{}, balance=balance+{} WHERE id={}".format(money, money, id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新用户余额失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_balance(self, money, id):
        sql = "UPDATE account set balance=balance+{} WHERE id={}".format(money, id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新用户余额失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_remove_free(self, user_id):
        sql = "UPDATE account set free=free-1 WHERE id={}".format(user_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新用户免费建卡数量失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def insert_top_up(self, pay_num, now_time, money, before_balance, balance, account_id, trans_type):
        sql = "INSERT INTO top_up(pay_num, time, money, before_balance, balance, account_id, trans_type) " \
              "VALUES ('{}','{}',{},{},{},{},'{}')".format(pay_num, now_time, money, before_balance, balance,
                                                           account_id, trans_type)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("插入用户充值记录失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def insert_pay_log(self, pay_time, pay_money, top_money, ver_code, status, phone, url, pic_json, account_id):
        sql = "INSERT INTO pay_log(pay_time, pay_money, top_money, ver_code, status, phone, url, pic_json, account_id) " \
              "VALUES ('{}',{},{},'{}','{}','{}', '{}','{}',{})".format(pay_time, pay_money, top_money, ver_code,
                                                                   status, phone, url, pic_json, account_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("插入用户请求充值信息失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_time_sum_money(self, x_time, user_id):
        sql = "SELECT money,trans_type FROM top_up WHERE account_id={} AND time <= '{}'".format(user_id, x_time)
        self.cursor.execute(sql)
        row = self.cursor.fetchall()
        res = 0
        for i in row:
            money = i[0]
            trans_type = i[1]
            if trans_type == '系统':
                res += money
        return res

    def search_top_history(self, sql_line):
        sql = "SELECT * FROM top_up LEFT JOIN account ON account.id=top_up.account_id {}".format(sql_line)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        else:
            for i in rows:
                info_dict = dict()
                info_dict['pay_num'] = '\t' + i[1]
                info_dict['time'] = str(i[2])
                info_dict['money'] = i[3]
                info_dict['before_balance'] = i[4]
                info_dict['balance'] = i[5]
                info_dict['user_id'] = i[6]
                info_dict['trans_type'] = i[7]
                info_dict['name'] = i[12]
                info_list.append(info_dict)
            return info_list

    def admin_info(self):
        sql = "SELECT account, password, name, balance FROM admin"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0], rows[0][1], rows[0][2], rows[0][3]

    def search_admin_field(self, field):
        sql = "SELECT {} FROM admin".format(field)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    def update_admin_field(self, field, value):
        sql = "UPDATE admin SET {}='{}'".format(field, value)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新ADMIN字段失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def insert_account(self, account, password, phone_num, name, create_price, refund, min_top, max_top, start_time, stop_time):
        sql = "INSERT INTO account(account, password, phone_num, name, create_price, refund, min_top, max_top, start_time, stop_time) " \
              "VALUES ('{}','{}','{}','{}',{},{},{},{},'{}','{}')".format(account, password, phone_num, name, create_price,
                                                                refund, min_top, max_top, start_time, stop_time)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加用户失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def del_account_info(self, user_id):
        sql = "DELETE FROM account WHERE id = {}".format(user_id)
        self.cursor.execute(sql)
        self.connect.commit()
        self.close_connect()

    def search_middle_ed(self, name):
        sql = "SELECT COUNT(*) FROM middle WHERE name ='{}'".format(name)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    def insert_middle(self, account, password, name, phone_num, card_price, note):
        sql = "INSERT INTO middle(account, password, name, phone_num, card_price, note) " \
              "VALUES ('{}','{}','{}','{}',{},'{}')".format(account, password, name, phone_num, card_price, note)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加中介失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_middle_info(self):
        sql = "SELECT * FROM middle"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        for i in rows:
            info_dict = dict()
            middle_id = i[0]
            info_dict['cus_num'] = self.search_acc_middle(middle_id)
            info_dict['account'] = i[1]
            info_dict['password'] = i[2]
            info_dict['name'] = i[3]
            info_dict['phone_num'] = i[4]
            info_dict['card_price'] = i[5]
            info_list.append(info_dict)
        return info_list

    def search_acc_middle(self, middle_id):
        sql = "SELECT COUNT(*) FROM account WHERE middle_id={}".format(middle_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    def search_acc_middle_null(self):
        sql = "SELECT name FROM account WHERE middle_id is null"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        cus_list = list()
        if not rows:
            return cus_list
        for i in rows:
            cus_list.append(i[0])
        return cus_list

    def search_cus_list(self, middle_name):
        sql = "SELECT account.`name` FROM account LEFT JOIN middle ON account.middle_id = middle.id WHERE " \
              "middle.`name`='{}'".format(middle_name)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        cus_list = list()
        if not rows:
            return cus_list
        for i in rows:
            cus_list.append(i[0])
        return cus_list

    def update_middle_field_int(self, field, value, name):
        sql = "UPDATE middle SET {} = {} WHERE name = '{}'".format(field, value, name)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新中介字段" + field + "失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_middle_field_str(self, field, value, name):
        sql = "UPDATE middle SET {} = '{}' WHERE name = '{}'".format(field, value, name)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新中介字段" + field + "失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_middle_name(self, field, name):
        sql = "SELECT {} FROM middle WHERE name='{}'".format(field, name)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    def search_name_info(self):
        sql = "SELECT last_name, female, man FROM name_info"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        last_name = list()
        female = list()
        for i in rows:
            last_name.append(i[0])
            female.append(i[1])
            female.append(i[2])
        info_dict = dict()
        info_dict['last_name'] = last_name
        info_dict['female'] = female
        return info_dict

    def search_middle_id(self):
        sql = "SELECT id FROM middle"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        for i in rows:
            info_list.append(i[0])
        return info_list

    def search_user_field_admin(self):
        sql = "SELECT id, name FROM account".format()
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        account_list = list()
        if not rows:
            return account_list
        for i in rows:
            info_dict = dict()
            info_dict['id'] = i[0]
            info_dict['name'] = i[1]
            account_list.append(info_dict)
        return account_list

    def search_middle_money_admin(self):
        sql = "SELECT middle_money.*, middle.`name` FROM middle_money LEFT JOIN middle ON middle.id = middle_money.middle_id"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        for i in rows:
            info_dict = dict()
            info_dict['id'] = i[0]
            info_dict['start_time'] = str(i[2])
            info_dict['end_time'] = str(i[3])
            info_dict['card_num'] = i[4]
            info_dict['create_price'] = i[5]
            info_dict['sum_money'] = i[6]
            info_dict['create_time'] = str(i[7])
            info_dict['pay_status'] = i[8]
            if i[9]:
                info_dict['pay_time'] = str(i[9])
            else:
                info_dict['pay_time'] = ""
            info_dict['name'] = i[12]
            info_list.append(info_dict)
        return info_list

    def update_middle_sub(self, pay_status, pay_time, info_id):
        sql = "UPDATE middle_money SET pay_status = '{}', pay_time = '{}' WHERE id = {}".format(pay_status, pay_time,
                                                                                                info_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新中介费确认失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_card_info_admin(self, sql_line):
        sql = "SELECT * FROM card_info ORDER BY act_time DESC {}".format(sql_line)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        for i in rows:
            info_dict = dict()
            info_dict['activation'] = i[1]
            if i[2]:
                info_dict['card_no'] = "\t" + i[2]
            else:
                info_dict['card_no'] = ""
            info_dict['pay_passwd'] = i[3]
            if i[4]:
                info_dict['act_time'] = str(i[4])
            else:
                info_dict['act_time'] = ""
            info_dict['card_name'] = i[5]
            info_dict['label'] = i[6]
            info_dict['expire'] = i[7]
            info_dict['cvv'] = i[8]
            if i[9]:
                name = self.search_user_field('name', i[9])
                info_dict['account_name'] = name
            else:
                info_dict['account_name'] = ""
            info_list.append(info_dict)
        return info_list

    def search_trans_admin(self, sql_all):
        sql = "SELECT account_trans.*, account.name FROM account_trans LEFT JOIN account ON account_trans.account_id" \
              " = account.id {}".format(sql_all)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        for i in rows:
            info_dict = dict()
            info_dict['date'] = str(i[1])
            info_dict['trans_type'] = i[2]
            info_dict['do_type'] = i[3]
            info_dict['num'] = i[4]
            info_dict['card_no'] = "\t" + i[5]
            info_dict['do_money'] = i[6]
            info_dict['hand_money'] = i[7]
            info_dict['before_balance'] = i[8]
            info_dict['balance'] = i[9]
            info_dict['cus_name'] = i[11]
            info_list.append(info_dict)
        return info_list

    def search_trans_sum_admin(self):
        sql = "SELECT SUM(do_money), SUM(hand_money) FROM account_trans WHERE trans_type='支出'"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows[0][0]:
            return 0
        do_money = rows[0][0]
        hand_money = rows[0][1]
        sum_money = do_money + hand_money
        return sum_money

    def search_user_sum_balance(self):
        sql = "SELECT  SUM(balance),SUM(sum_balance) FROM account"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0], rows[0][1]

    def insert_account_log(self, n_time, customer, balance, out_money, sum_balance):
        sql = "INSERT INTO account_log(log_time, customer, balance, out_money, sum_balance) VALUES ('{}','{}',{},{},{})".format(
            n_time, customer, balance, out_money, sum_balance)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加用户余额记录失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_account_log(self, cus_sql, time_sql):
        sql = "SELECT * FROM account_log WHERE log_time != '' {} {}".format(cus_sql, time_sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        info_list = list()
        if not rows:
            return info_list
        for i in rows:
            info_dict = dict()
            info_dict['log_time'] = str(i[1])
            info_dict['customer'] = i[2]
            info_dict['balance'] = i[3]
            info_dict['out_money'] = i[4]
            info_dict['sum_balance'] = i[5]
            info_list.append(info_dict)
        return info_list

    def search_card_status(self, sql_line):
        sql = "SELECT COUNT(*) FROM card_info {}".format(sql_line)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    def search_card_remain_admin(self):
        sql = "SELECT SUM(remain) FROM card_info"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return 0
        return rows[0][0]

    def search_trans_sum_admin(self):
        sql = "SELECT SUM(do_money) FROM account_trans"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows[0][0]:
            return 0
        sum_money = round(rows[0][0], 2)
        return sum_money

    # 以下是带充值需要使用的方法----------------------------------------------------------------------------------------
    def search_pay_log(self, status, sql_time=''):
        sql = "SELECT pay_time,pay_money,top_money,top_up.before_balance,top_up.balance,pay_log.`status`,ver_time,url," \
              "account.`name`,pic_json,account.id FROM pay_log LEFT JOIN account ON pay_log.account_id=account.id " \
              "LEFT JOIN top_up on pay_log.account_id=top_up.account_id AND pay_log.ver_time=top_up.time " \
              "WHERE pay_log.`status`='{}' {}".format(status, sql_time)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return
        info_list = list()
        for i in rows:
            info_dict = dict()
            info_dict['pay_time'] = str(i[0])
            info_dict['pay_money'] = i[1]
            info_dict['top_money'] = i[2]
            info_dict['before_balance'] = i[3]
            info_dict['balance'] = i[4]
            info_dict['status'] = i[5]
            info_dict['ver_time'] = str(i[6])
            info_dict['url'] = i[7]
            info_dict['cus_name'] = i[8]
            info_dict['pic_json'] = i[9]
            info_dict['cus_id'] = i[10]
            info_list.append(info_dict)
        return info_list

    def search_pay_code(self, field, cus_name, pay_time):
        sql = "SELECT {} from pay_log LEFT JOIN account ON pay_log.account_id=account.id WHERE account.`name`='{}' " \
              "AND pay_time='{}'".format(field, cus_name, pay_time)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return ''
        return rows[0][0]

    def update_pay_status(self, pay_status, t, cus_name, pay_time):
        sql = "UPDATE pay_log SET status='{}',ver_time='{}' WHERE account_id={} AND pay_time='{}'".format(pay_status, t,
                                                                                                          cus_name,
                                                                                                          pay_time)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("确认充值状态失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_pay_money(self, money, cus_name, pay_time):
        sql = "UPDATE pay_log SET top_money={} WHERE account_id={} AND pay_time='{}'".format(money, cus_name, pay_time)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("确认充值状态失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def del_pay_log(self, user_id, pay_time):
        sql = "DELETE FROM pay_log WHERE account_id = {} AND pay_time='{}'".format(user_id, pay_time)
        self.cursor.execute(sql)
        self.connect.commit()
        self.close_connect()

    def search_ac_trans(self):
        sql = "SELECT * from account_trans where account_id=176"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return
        info_list = list()
        for i in rows:
            info_dict = dict()
            info_dict['id'] = str(i[0])
            info_dict['trans_type'] = str(i[2])
            info_dict['do_money'] = i[6]
            info_list.append(info_dict)
        return info_list

    def update_money(self, be, bl, trans_id):
        sql = "UPDATE account_trans SET before_balance={}, balance={} WHERE id={}".format(be, bl, trans_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("确认充值状态失败!" + str(e))
            self.connect.rollback()
        # self.close_connect()

    # 收款码的插入和查询方法---------------------------------------------------------------------------------------------
    def insert_qr_code(self, url, up_date):
        sql = "INSERT INTO qr_code(url, up_date) VALUES('{}', '{}')".format(url, up_date)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加收款二维码失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_qr_code(self, sql):
        sql = "SELECT * FROM qr_code {}".format(sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        info_list = list()
        for i in rows:
            info_dict = dict()
            info_dict['qr_code'] = i[1]
            info_dict['qr_date'] = str(i[2])
            info_dict['sum_money'] = i[3]
            if i[4] == 0:
                info_dict['status'] = '正常'
            else:
                info_dict['status'] = '锁定'
            info_list.append(info_dict)
        return info_list

    def search_qr_field(self, field, url):
        sql = "SELECT {} FROM qr_code WHERE url='{}'".format(field, url)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        return rows[0][0]

    def search_table_count(self, table_name):
        sql = "SELECT COUNT(*) FROM {}".format(table_name)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    def update_qr_info(self, file, value, url):
        sql = "UPDATE qr_code SET {}={} WHERE url='{}'".format(file, value, url)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新收款码状态失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_qr_money(self, file, value, url):
        sql = "UPDATE qr_code SET {}={}+{} WHERE url='{}'".format(file, file, value, url)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新收款码金额失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def del_qr_code(self, url):
        sql = "DELETE FROM qr_code WHERE url = '{}'".format(url)
        self.cursor.execute(sql)
        self.connect.commit()
        self.close_connect()

    def update_1(self, hand_money, u_id):
        sql = "UPDATE account_trans SET hand_money={} WHERE id={}".format(hand_money, u_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("确认充值状态失败!" + str(e))
            self.connect.rollback()

    def search_1(self):
        sql = "SELECT id, hand_money FROM account_trans WHERE hand_money<0"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        for i in rows:
            s.update_1(abs(i[1]), i[0])

    # 推送信息相关----------------------
    def insert_push_log(self, trade_no, card_no, trans_type, timestamp, local_merchant_name, trans_amount,
                        trans_currency_type, settle_amount, settle_currency_type, trans_status, account_id):
        sql = "INSERT INTO push_log(trade_no, card_no, trans_type, timestamp, local_merchant_name, trans_amount, " \
              "trans_currency_type, settle_amount, settle_currency_type, trans_status, account_id) VALUES('{}','{}'," \
              "'{}','{}','{}','{}','{}','{}','{}','{}',{})".format(trade_no, card_no, trans_type, timestamp,
                                                                   local_merchant_name, trans_amount,
                                                                   trans_currency_type, settle_amount,
                                                                   settle_currency_type, trans_status, account_id)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加推送交易失败!" + sql)
            self.connect.rollback()
        self.close_connect()

    def search_user_push(self, user_id, sql):
        sql = "SELECT * FROM push_log WHERE account_id={} {}".format(user_id, sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        info_list = list()
        for i in rows:
            info_dict = dict()
            info_dict['trade_no'] = "\t" + i[1]
            info_dict['card_no'] = "\t" + i[2]
            info_dict['trans_type'] = i[3]
            info_dict['timestamp'] = str(i[4])
            info_dict['local_merchant_name'] = i[5]
            info_dict['trans_amount'] = i[6]
            info_dict['trans_currency_type'] = i[7]
            info_dict['settle_amount'] = i[8]
            info_dict['settle_currency_type'] = i[9]
            info_dict['trans_status'] = i[10]
            info_list.append(info_dict)
        return info_list

    def search_push(self, sql_line):
        sql = "SELECT push_log.*, account.name FROM push_log LEFT JOIN account ON push_log.account_id = account.id {}".format(sql_line)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        info_list = list()
        for i in rows:
            info_dict = dict()
            info_dict['trade_no'] = "\t" + i[1]
            info_dict['card_no'] = "\t" + i[2]
            info_dict['trans_type'] = i[3]
            info_dict['timestamp'] = str(i[4])
            info_dict['local_merchant_name'] = i[5]
            info_dict['trans_amount'] = i[6]
            info_dict['trans_currency_type'] = i[7]
            info_dict['settle_amount'] = i[8]
            info_dict['settle_currency_type'] = i[9]
            info_dict['trans_status'] = i[10]
            info_dict['account_name'] = i[12]
            info_list.append(info_dict)
        return info_list

    def insert_account_reg(self, package, pay_time, start_time, reg_money, reg_days, stop_time, u_name, u_acc, u_pass,
                           phone, url, middle_id, middle_name, pic_json, ver_code):
        sql = "INSERT INTO account_reg(package, pay_time, start_time, reg_money, reg_days, stop_time, u_name, u_acc, u_pass," \
              " phone ,url, middle_id, middle_name, pic_json, ver_code) VALUES ('{}','{}','{}',{},{},'{}','{}','{}','{}'," \
              "'{}','{}',{},'{}','{}','{}')".format(package, pay_time, start_time, reg_money, reg_days, stop_time,
                                                     u_name, u_acc, u_pass, phone, url, middle_id, middle_name,
                                                     pic_json, ver_code)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("插入用户注册信息失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    # ------------------操作注册套餐的方法-----

    def search_reg_package(self):
        sql = "SELECT package FROM reg_money"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return []
        info_list = list()
        for i in rows:
            info_list.append(i[0])
        return info_list

    def update_reg_field(self, field, value, package):
        sql = "UPDATE reg_money SET {}={} WHERE package='{}'".format(field, value, package)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新注册金额失败!" + str(e))
            self.connect.rollback()

    def insert_reg_package(self, package, money, days, price, refund, min_top, max_top):
        sql = "INSERT  INTO reg_money(package, money, days, price, refund, min_top, max_top) VALUES('{}', {},{}," \
              "{},{},{},{})".format(package, money, days, price, refund, min_top, max_top)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加注册套餐失败!" + str(e))
            self.connect.rollback()

    def del_reg_package(self, package):
        sql = "DELETE FROM reg_money WHERE package = '{}'".format(package)
        self.cursor.execute(sql)
        self.connect.commit()
        self.close_connect()

    def search_reg_money(self, package):
        sql = "SELECT * FROM reg_money WHERE package='{}'".format(package)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return {}
        else:
            info_dict = dict()
            info_dict['package'] = rows[0][1]
            info_dict['money'] = rows[0][2]
            info_dict['days'] = rows[0][3]
            info_dict['price'] = rows[0][4]
            info_dict['refund'] = rows[0][5]
            info_dict['min_top'] = rows[0][6]
            info_dict['max_top'] = rows[0][7]
            return info_dict

    def search_reg_all(self):
        sql = "SELECT * FROM reg_money"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return {}
        info_list = list()
        for row in rows:
            info_dict = dict()
            info_dict['package'] = row[1]
            info_dict['money'] = row[2]
            info_dict['days'] = row[3]
            info_dict['price'] = row[4]
            info_dict['refund'] = row[5]
            info_dict['min_top'] = row[6]
            info_dict['max_top'] = row[7]
            info_list.append(info_dict)
        return info_list

    def search_account_reg(self, status, sql_line=''):
        sql = "SELECT * FROM account_reg WHERE status='{}' {}".format(status, sql_line)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        info_list = list()
        for i in rows:
            info_dict = dict()
            info_dict['package'] = i[1]
            info_dict['pay_time'] = str(i[2])
            info_dict['start_time'] = str(i[3])
            info_dict['reg_money'] = i[4]
            info_dict['reg_days'] = i[5]
            info_dict['stop_time'] = str(i[6])
            info_dict['u_name'] = i[7]
            info_dict['phone'] = i[10]
            info_dict['url'] = i[11]
            info_dict['middle_name'] = i[13]
            info_dict['pic_json'] = i[14]
            info_dict['status'] = i[16]
            info_list.append(info_dict)
        return info_list

    def search_account_reg_field(self, field, pay_time, u_name):
        sql = "SELECT {} FROM account_reg WHERE pay_time='{}' AND u_name='{}'".format(field, pay_time, u_name)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        if not rows:
            return False
        else:
            return rows[0][0]

    def update_account_reg_field(self, field, value, pay_time, u_name):
        sql = "UPDATE account_reg SET {}='{}' WHERE pay_time='{}' AND u_name='{}'".format(field, value, pay_time, u_name)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("确认注册状态失败!" + str(e))
            self.connect.rollback()



if __name__ == "__main__":
    s = SqlData()

    '''
    根据账户消费记录,重新计算当前余额(在扣费异常时使用)
    
    
    before = 4341.53
    info = s.search_ac_trans()
    print(info)
    for i in info:
        trans_id = i.get('id')
        trans_type = i.get('trans_type')
        do_money = i.get('do_money')
        if trans_type == '支出':
            balance = round(before - float(do_money), 2)
        elif trans_type == '收入':
            balance = round(before + float(do_money), 2)
        s.update_money(before, balance, trans_id)
        print(before, balance)
        before = balance
    '''

    # q = QuanQiuFu()
    # card_info = s.search_card_info_admin('WHERE account_id=45')
    # card_list = list()
    # for i in card_info:
    #     card_no = i.get('card_no').strip()
    #     card_id = i.get('card_id')
    #     print(card_no)
    #     if card_no not in card_list:
    #         card_list.append(card_no)
    #     else:
    #         s.del_card_info(card_id)

    '''
    计算客户消费金额和余额是否匹配总充值金额
    
    task_one = SqlData().search_account_info('')
    task_info = list()
    print(task_one)
    for u in task_one:
        u_id = u.get('u_id')
        card_count = SqlData().search_card_count(u_id, '')
        out_money = SqlData().search_trans_sum(u_id)
        u['card_num'] = card_count
        u['out_money'] = out_money
        balance = u['balance']
        sum_balance = u['sum_balance']
        name = u['name']
        if round(balance + out_money, 2) == sum_balance:
            res = '正常'
        else:
            res = '错误'
            print(balance, out_money, balance + out_money, sum_balance, sum_balance - balance - out_money, res, name)
    '''


