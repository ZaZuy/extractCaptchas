import numpy as np
from tensorflow.python.ops.numpy_ops import np_config
import tensorflow as tf
import requests
import json
import keras
from keras import layers
import base64
from PIL import Image

import io
class CaptchaSolver:
    def __init__(self):
        self.batch_size = 20
        self.img_width = 280
        self.img_height = 70
        self.max_length = 6

        self.char_ = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'a', 'b', 'c', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'n', 'p', 'q', 's', 't', 'u', 'v', 'x', 'y', 'z']
        self.char_to_num = layers.experimental.preprocessing.StringLookup(
            vocabulary=list(self.char_), num_oov_indices=1
        )
        self.num_to_char = layers.experimental.preprocessing.StringLookup(
            vocabulary=self.char_to_num.get_vocabulary(), invert=True
        )
        self.url = 'http://10.5.0.5:8601/v1/models/solveCaptchas:predict'

    def encode_single_sample(self, img_path, label):
        img = tf.io.read_file(img_path)
        img = tf.io.decode_png(img, channels=1)
        img = tf.image.convert_image_dtype(img, tf.float32)
        img = tf.image.resize(img, [self.img_height, self.img_width])
        img = tf.transpose(img, perm=[1, 0, 2])
        label = self.char_to_num(tf.strings.unicode_split(label, input_encoding="UTF-8"))
        label = tf.pad(label, [[0, self.max_length - tf.shape(label)[0]]])
        return {"image": img, "label": label}

    def decode_batch_predictions(self, pred):
        input_len = np.ones(pred.shape[0]) * pred.shape[1]
        results = tf.keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :self.max_length]
        output_text = []
        for res in results:
            res = tf.strings.reduce_join(self.num_to_char(res)).numpy().decode("utf-8")
            output_text.append(res)
        return output_text

    def preprocess_base64_image(self, base64_data):
        image_data = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_data))
        img = image.convert("L")
        img = img.resize((self.img_width, self.img_height))
        img = np.array(img)
        img = img.astype(np.float32) / 255.0
        img = tf.convert_to_tensor(img)
        img = tf.transpose(img, perm=[1, 0])
        img = tf.expand_dims(img, axis=-1)
        return img

    def make_prediction(self, base64_string):
        img = self.preprocess_base64_image(base64_string)
        np_config.enable_numpy_behavior()
        zeros_array = np.zeros((1, self.max_length))
        instances = [
            {
                "image": img.tolist(),
                "label": zeros_array.tolist()
            }
        ]
        data = json.dumps({"signature_name": "serving_default", "instances": instances})
        headers = {'Content-Type': 'application/json'}
        json_response = requests.post(self.url, data=data, headers=headers)
        predictions = json.loads(json_response.text)['predictions']
        arr_img = np.array(predictions)
        predictions = self.decode_batch_predictions(arr_img)
        return predictions