from datetime import timedelta
from flask import Flask
import logging
from celery import Celery
from flask_caching import Cache
from tools_me.parameter import DIR_PATH

app = Flask(__name__)
# 使用缓存,缓存大量查出来的信息
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

app.config['SECRET_KEY'] = 'Gute9878934'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

app.app_context().push()
# CSRFProtect(app)


asyn = Celery('task', broker='redis://localhost:6379')

LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(pathname)s %(message)s "  # 配置输出日志格式
DATE_FORMAT = '%Y-%m-%d  %H:%M:%S %a '  # 配置输出时间的格式，注意月份和天数不要搞乱了
logging.basicConfig(level=logging.ERROR,
                    format=LOG_FORMAT,
                    datefmt=DATE_FORMAT,
                    filename=DIR_PATH.LOG_PATH  # 有了filename参数就不会直接输出显示到控制台，而是直接写入文件
                    )

# 注册路由,以url_prefix区分功能(蓝图)

from apps.user import user_blueprint

app.register_blueprint(user_blueprint)

from apps.middle import middle_blueprint

app.register_blueprint(middle_blueprint)

from apps.admin import admin_blueprint

app.register_blueprint(admin_blueprint)

from apps.pay import pay_blueprint

app.register_blueprint(pay_blueprint)

from apps.verify_pay import verify_pay_blueprint

app.register_blueprint(verify_pay_blueprint)


