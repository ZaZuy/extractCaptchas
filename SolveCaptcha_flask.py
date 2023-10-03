import json

import utils, config
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/v1/captcha/', methods=['GET'])
def welcome():
    res = utils.CaptchaSolver.make_prediction(utils.CaptchaSolver(), config.base64)
    return json.dumps(
        {
            "code": 200,
            "result": res
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
