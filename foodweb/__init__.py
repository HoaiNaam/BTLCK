from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
from flask_babelex import Babel
import cloudinary
import base64, os

app = Flask(__name__)
app.secret_key = '689567gh$^^&*#%^&*^&%^*DFGH^&*&*^*'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%s@localhost/foodappdb?charset=utf8mb4' % quote('Nguyenhoainam10')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['CART_KEY'] = 'cart'

cloudinary.config(cloud_name='djx6d4r2r', api_key='413495573627426', api_secret='YCLu93ObZ0VwE-A6z1B49C7sK4Q')

db = SQLAlchemy(app=app)

login = LoginManager(app=app)

babel = Babel(app=app)

MY_AES_KEY = b'W008gXDES2_xAnDNIdnFFeUa-6z-suOkc3UOlRpuJD4='

SITE_KEY_V2 = "6LeE7qorAAAAANnfXIu99uAb4xCD89ik6ftM3RQ0"
SECRET_KEY_V2 ="6LeE7qorAAAAABvDzOrtXULQzf_ev4YsroPpinNH"

SITE_KEY_V3 = "6LeW7qorAAAAALIStVmJ1yuHutdd9JAmqoVH-Gmw"
SECRET_KEY_V3 ="6LeW7qorAAAAALZxfOdFbvtCvZov_-19CgSDsG9s"

app.config['RECAPTCHA_PUBLIC_KEY'] = SITE_KEY_V2
app.config['RECAPTCHA_PRIVATE_KEY'] = SECRET_KEY_V2





@babel.localeselector
def load_locale():
    return 'vi'

# MY_AES_KEY = base64.urlsafe_b64encode(os.urandom(32))
# print(MY_AES_KEY)