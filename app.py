from flask import Flask
import Backend.routes.admin as admin
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='Frontend/templates', static_folder='Frontend/static')
app.secret_key = os.getenv('SECRET_KEY')
app.register_blueprint(admin.admin)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')