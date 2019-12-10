# coding:utf-8
# 以下是一些常用参数
import os

# 获取项目的文件的绝对路径,使配置文件路径为绝对路径,避免card_remain模块单独使用异常
file_pwd = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class DIR_PATH:
    LOG_PATH = file_pwd + "/static/log/card.log"
    # LOG_PATH = "static/log/card.log"

    # PRI_PEM = "G:\\world_pay\\static\\api_key\\privkey_henry.pem"
    PRI_PEM = file_pwd + "/static/api_key/privkey_henry.pem"

    # PUB_PEM = 'G:\\world_pay\\static\\api_key\\pro_epaylinks_publickey.pem'
    PUB_PEM = file_pwd + "/static/api_key/pro_epaylinks_publickey.pem"

    # PHOTO_DIR = 'G:/world_pay/static/pay_pic/'
    PHOTO_DIR = file_pwd + "/static/pay_pic/"
    #
    # XLS_PATH = '/world_pay/static/top_xls/'
    XLS_PATH = file_pwd + '/static/top_xls/'

    # DOWNLOAD = 'G:\world_pay\static\download\world_pay_demo.xls'
    DOWNLOAD = file_pwd + '/static/download/world_pay_demo.xls'


class RET:
    OK = 0
    SERVERERROR = 502


class MSG:
    OK = 'SUCCESSFUL'
    SERVERERROR = 'SERVER ERROR'
    NODATA = 'NODATA'
    DATAERROR = '参数错误!'
    PSWDERROR = 'PASS_WORD ERROR'
    PSWDLEN = '密码长度不得小于6位数!'


class CACHE:
    TIMEOUT = 15


class TASK:
    SUM_ORDER_CODE = ''


class ORDER:
    TASK_CODE = ''
    BUY_ACCOUNT = ''
    TERRACE = ''
    COUNTRY = ''
    LAST_BUY = ''
    STORE = ''
    ASIN = ''
    STORE_GROUP = ''
    ASIN_GROUP = ''


TRANS_STATUS = {
    'WAIT': '待付款',
    'PROCESS': '处理中',
    'PAID': '已付款',
    'SUBBANK': '已提交银行',
    'SUCC': '交易成功',
    'FINISH': '交易完成',
    'AUTH': '已授权',
    'FAIL': '交易失败',
    'CLOSED': '交易关闭'
}


TRANS_TYPE_LOG = {
    '10B1': '换续卡手续费',
    '10B2': '休眠账户管理费',
    '10B3': '过期账户管理费',
    '10B4': '余额领回服务费',
    '10B5': '注销账户服务费',
    '10A8': '手续费',
    '0100': '充值',
    '0102': '在线充值',
    '0110': '礼品卡激活',
    '0200': '消费',
    '0201': '授权消费',
    '0202': '授权清算',
    '0203': '补扣款',
    '0205': 'ATM提款授权',
    '0206': 'ATM提款清算',
    '0302': '退款',
    '0303': '拒付',
    '0308': '网关支付退款',
    '0400': '转账',
    '0402': '他行转账',
    '0500': '提现',
    '0600': '转账到银行卡',
    '0601': '商户转账到银行卡',
    '0701': '交易状态查询',
    '0702': '查询余额',
    '0800': '网关支付',
    '0920': '消费撤销',
    '0921': '消费授权撤销',
    '0922': '人工授权撤销',
    '0923': '自动授权撤销',
    '0932': '退款撤销',
    '0933': '拒付撤销',
}


class TRANS_TYPE:
    IN = "收入"
    OUT = "支出"


class DO_TYPE:
    CREATE_CARD = "开卡"
    TOP_UP = "充值"
    REFUND = "退款"
    CARD_LOCK = '11'
    CARD_OPEN = '12'
