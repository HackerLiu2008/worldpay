import hashlib
import logging
import os
import rsa
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import MD5
import base64, requests, datetime, time


file_pwd = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class DIR_PATH(object):
    PRI_PEM = file_pwd + "/static/api_key/privkey_henry.pem"
    PUB_PEM = file_pwd + "/static/api_key/pro_epaylinks_publickey.pem"


class QuanQiuFu(object):
    def __init__(self):
        self.url = "https://www.globalcash.cn/openapi/service"
        self.ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def api_requests(self, data):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        # proxies = {
        #     'http': 'http://159.138.55.160:27926'
        # }
        res = requests.post(self.url, data=data, headers=headers, timeout=20)
        return res

    def rsa_sign(self, data):
        # MD5withrsa加密方式
        private_key_file = open(DIR_PATH.PRI_PEM, 'r')
        pri_key = RSA.importKey(private_key_file.read())
        signer = PKCS1_v1_5.new(pri_key)
        hash_obj = self.my_hash(data)
        signature = base64.b64encode(signer.sign(hash_obj))
        private_key_file.close()
        return signature

    # def rsa_verify(self, signature, data):
    #     public_key_file = open('pro_epaylinks_publickey.pem', 'r')
    #     pub_key = RSA.importKey(public_key_file.read())
    #     hash_obj = self.my_hash(data)
    #     verifier = PKCS1_v1_5.new(pub_key)
    #     public_key_file.close()
    #     return verifier.verify(hash_obj, base64.b64decode(signature))

    def md5_rsa(self, pay_passwd, is_pass):
        '''
        :param pay_passwd:   加密的数据
        :param is_pass:  对 是否密码o
        '''

        with open(DIR_PATH.PUB_PEM, 'r') as file_pub:
            f_pub = file_pub.read()
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(f_pub.encode())
        if is_pass:
            # 若是密码则MD5
            m = hashlib.md5()
            m.update(pay_passwd.encode())
            pay_passwd = m.hexdigest()
        crypt = rsa.encrypt(pay_passwd.encode('utf-8'), pubkey)
        return base64.b64encode(crypt)

    def pay_passwd(self, pass_word):
        pay_passwd = self.md5_rsa(pass_word, is_pass=True)
        return pay_passwd.decode()

    def my_hash(self, data):
        return MD5.new(data.encode('utf-8'))

    def kv_list(self, data):
        #  字符串拼接
        sort_keys = sorted(data.keys())
        kv_list = []
        for key in sort_keys:
            kv_list.append(str(key) + '=' + str(data[key]))
        data_str = '&'.join(kv_list)
        sign = self.rsa_sign(data_str)
        return sign

    def create_card(self, activation, pass_word):
        # 卡开通
        # 流水号item_id
        itme_id = self.get_order_code()
        data = {
            'api_name': 'epaylinks_umps_user_open_account',
            'ver': '1.0',
            'format': 'json',
            'app_id': 'tjvdm5wlX2oKN8rB8idvA2Fi',
            'terminal_no': '36248614',
            'timestamp': self.ts,
            'pay_passwd': self.pay_passwd(pass_word),
            'receive_card_no': activation,
            'busi_water_no': itme_id,
        }
        sign = self.kv_list(data)
        data['sign'] = sign.decode()
        try:
            res = self.api_requests(data)
            return res.json()
        except Exception as e:
            logging.error("开卡接口异常:" + str(e) + "data: " + str(data))
            info_dict = {'resp_code': '9999', "resp_msg": '服务器繁忙!'}
            return info_dict

    def query_card_info(self, card_num):
        # 全球付卡信息查询
        data = {
            'api_name': 'epaylinks_umps_user_query_acct_info',
            'ver': '1.0',
            'format': 'json',
            'app_id': 'tjvdm5wlX2oKN8rB8idvA2Fi',
            'terminal_no': '36248614',
            'timestamp': self.ts,
            'card_no': card_num,
        }
        sign = self.kv_list(data)
        data['sign'] = sign.decode()
        try:
            res = self.api_requests(data)
            return res.json()
        except Exception as e:
            logging.error("卡信息查询接口异常:" + str(e) + "data: " + str(data))
            info_dict = {'resp_code': '9999', "resp_msg": '服务器繁忙!'}
            return info_dict

    def query_tran_detail(self, card_num):
        # 收支明细查询
        data = {
            'api_name': 'epaylinks_umps_user_query_tran_detail',
            'ver': '1.0',
            'format': 'json',
            'app_id': 'tjvdm5wlX2oKN8rB8idvA2Fi',
            'terminal_no': '36248614',
            'timestamp': self.ts,
            'card_no': card_num,
            'begin_time': '20191009120001'
        }
        sign = self.kv_list(data)
        data['sign'] = sign.decode()
        try:
            res = self.api_requests(data)
            return res.json()
        except Exception as e:
            logging.error("卡收支明细接口异常:" + str(e) + "data: " + str(data))
            info_dict = {'resp_code': '9999', "resp_msg": '服务器繁忙!'}
            return info_dict

    def auth_trade_query(self, card_num):
        # 交易记录查询
        data = {
            'api_name': 'epaylinks_umps_user_auth_trade_query',
            'ver': '1.0',
            'format': 'json',
            'count_per_page': '1000',
            'app_id': 'tjvdm5wlX2oKN8rB8idvA2Fi',
            'terminal_no': '36248614',
            'timestamp': self.ts,
            'card_no': card_num,
            'query_type': '4',
            'end_time': self.ts,
        }
        sign = self.kv_list(data)
        data['sign'] = sign.decode()
        try:
            res = self.api_requests(data)
            return res.json()
        except Exception as e:
            logging.error("卡交易记录接口异常:" + str(e) + "data: " + str(data))
            info_dict = {'resp_code': '9999', "resp_msg": '服务器繁忙!'}
            return info_dict

    def trans_account_recharge(self, card_num, money):
        # 代充值
        # mer_order商户订单号
        mer_order = self.get_order_code()
        data = {
            'api_name': 'epaylinks_trans_account_recharge',
            'ver': '1.0',
            'format': 'json',
            'app_id': 'tjvdm5wlX2oKN8rB8idvA2Fi',
            'terminal_no': '36248614',
            'timestamp': self.ts,
            'card_no': card_num,
            'trans_type': '0100',
            'trans_sub_type': "03",
            'mer_order_no': mer_order,
            'order_amount': money
        }
        sign = self.kv_list(data)
        data['sign'] = sign.decode()
        try:
            res = self.api_requests(data)
            return res.json()
        except Exception as e:
            logging.error("卡充值接口异常:" + str(e) + "data: " + str(data))
            info_dict = {'resp_code': '9999', "resp_msg": '服务器繁忙!'}
            return info_dict

    def trans_account_cinsume(self, card_num, pass_word, money):
        # 卡余额消费
        # mer_order商户订单号
        mer_order = self.get_order_code()
        pay_passwd = self.pay_passwd(pass_word)
        data = {
            'api_name': 'epaylinks_trans_account_consume',
            'ver': '1.0',
            'format': 'json',
            'app_id': 'tjvdm5wlX2oKN8rB8idvA2Fi',
            'terminal_no': '36248614',
            'timestamp': self.ts,
            'card_no': card_num,
            'trans_type': '0200',
            'trans_sub_type': "03",
            'mer_order_no': mer_order,
            'order_amount': money,
            'pay_passwd': pay_passwd
        }
        sign = self.kv_list(data)
        data['sign'] = sign.decode()
        try:
            res = self.api_requests(data)
            return res.json()
        except Exception as e:
            logging.error("卡余额领会接口异常:" + str(e) + "data: " + str(data))
            info_dict = {'resp_code': '9999', "resp_msg": '服务器繁忙!'}
            return info_dict

    def card_loss(self, card_num, pass_word, loss_type):
        mer_order = self.get_order_code()
        pay_passwd = self.pay_passwd(pass_word)
        data = {
            'api_name': 'epaylinks_umps_user_card_loss',
            'ver': '1.0',
            'format': 'json',
            'app_id': 'tjvdm5wlX2oKN8rB8idvA2Fi',
            'terminal_no': '36248614',
            'timestamp': self.ts,
            'card_no': card_num,
            'pay_passwd': pay_passwd,
            'busi_water_no': mer_order,
            'oper_type': loss_type
        }
        sign = self.kv_list(data)
        data['sign'] = sign.decode()
        try:
            res = self.api_requests(data)
            return res.json()
        except Exception as e:
            logging.error("卡挂失接口异常:" + str(e) + "data: " + str(data))
            info_dict = {'resp_code': '9999', "resp_msg": '服务器繁忙!'}
            return info_dict

    def card_status_query(self, card_no):
        data = {
            'api_name': 'epaylinks_umps_user_status_query',
            'ver': '1.0',
            'format': 'json',
            'app_id': 'tjvdm5wlX2oKN8rB8idvA2Fi',
            'terminal_no': '36248614',
            'timestamp': self.ts,
            'card_no': card_no,
        }
        sign = self.kv_list(data)
        data['sign'] = sign.decode()
        try:
            res = self.api_requests(data)
            return res.json()
        except Exception as e:
            logging.error("卡挂失接口异常:" + str(e) + "data: " + str(data))
            info_dict = {'resp_code': '9999', "resp_msg": '服务器繁忙!'}
            return info_dict

    def get_order_code(self):
        # 最后一位补上用户id
        order_no = str(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))) + str(time.time()).replace('.', '')[
                                                                                     -7:]
        # 卡余额退回在订单号第一位加上R
        time.sleep(0.001)
        return order_no


if __name__ == '__main__':
    qqf = QuanQiuFu()
    pay_passwd = '04A5E788'
    card_no = '64823085058061'

    resp = qqf.api_requests({})
    print(resp)
    # resp = qqf.trans_account_recharge('5295871079074495', '2000')

