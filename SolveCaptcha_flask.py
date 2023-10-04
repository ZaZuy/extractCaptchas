import json

import utils, config
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/v1/captcha/', methods=['POST'])
def welcome():
    base64 = request.form.get('data')
    res = utils.CaptchaSolver.make_prediction(utils.CaptchaSolver(), base64)
    return json.dumps(
        {
            "code": 200,
            "result": res[0]
        }
    )

if __name__ == '__main__':
    app.run(debug=True, host="10.5.0.4", port=5000) #debug for change code realtime update
