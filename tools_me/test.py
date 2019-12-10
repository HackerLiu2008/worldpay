import poplib
import random
import re
from email.parser import Parser

import requests
import datetime
'''
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/54.0.2840.99 Safari/537.36',
           'Cookie': "userName=PC190923US1530; route=e062ed5a095364733e85c54c9ce5238f; JSESSIONID=F39B1F0973523682F06F2EF0672A0693.node919", }
resp = requests.get('https://merchant.globalcash.cn/space/space.do', headers=headers)

res = re.findall('<em>(.*)</em>', resp.text)

print(res, resp.text)



email = 'globalcash@163.com'
passwd = 'goodsaler123'
pop3_server = 'pop.163.com'

# 连接到POP3服务器:
server = poplib.POP3(pop3_server)
# 可以打开或关闭调试信息:
server.set_debuglevel(1)
# 可选:打印POP3服务器的欢迎文字:
# print(server.getwelcome().decode('utf-8'))

# 身份认证:
server.user(email)
server.pass_(passwd)

# stat()返回邮件数量和占用空间:
# print('Messages: %s. Size: %s' % server.stat())
# list()返回所有邮件的编号:
resp, mails, octets = server.list()
# 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
# print(mails)

# 获取最新一封邮件, 注意索引号从1开始:
index = len(mails)
# print(index)
resp, lines, octets = server.retr(index-6)

# print(resp, bytes.decode(lines[0]), octets)

# lines存储了邮件的原始文本的每一行,
# 可以获得整个邮件的原始文本:
msg_content = b'\r\n'.join(lines).decode('gbk')

print(lines)
# 稍后解析出邮件:
msg = Parser().parsestr(msg_content)

# print(msg)

# 可以根据邮件索引号直接从服务器删除邮件:
# server.dele(index)
# 关闭连接:
server.quit()
'''

s = "http://127.0.0.1:5000/user/register/?middle_key=eWFuZ2ppbmxp"




