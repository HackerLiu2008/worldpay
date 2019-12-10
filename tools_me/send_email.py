# coding=utf-8
import logging
import smtplib  # 引入SMTP协议包
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  # 创建包含多个部分的邮件体
from email.mime.image import MIMEImage
from tools_me.parameter import DIR_PATH
from config import asyn

# msg_to = "2404052713@qq.com"  # 收件人邮箱

# 使用celery异步任务发送邮件,避免阻塞


@asyn.task
def send(context, pic_list, msg_to):
    msg_from = "3223750580@qq.com"  # 发送方邮箱
    passwd = "avjubvfehybzcifg"  # 填入发送方邮箱的授权码
    subject = "全球付"  # 主题
    msg = MIMEMultipart('related')
    image_tent = ""
    for i in range(len(pic_list)):
        image_tent += '<img src="cid:' + str(i) + '" alt="' + str(i) + '">'

    content = MIMEText('<html><body><div>' + context + '</div>' + image_tent + '</body></html>',
                       'html', 'utf-8')  # 正文

    msg.attach(content)
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to

    index = 0
    for pic in pic_list:
        pic_path = DIR_PATH.PHOTO_DIR + pic
        file = open(pic_path, "rb")
        img_data = file.read()
        file.close()
        img = MIMEImage(img_data)
        imgid = str(index)
        img.add_header('Content-ID', imgid)
        msg.attach(img)
        index += 1

    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮件服务器及端口号
        s.login(msg_from, passwd)
        s.sendmail(msg_from, msg_to, msg.as_string())
        return True
    except Exception as e:
        logging.error(e)
        return False
