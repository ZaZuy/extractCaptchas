import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import keras
from keras import models
from keras import layers

# path = "./400k/"
labels = []
images = []
# for file in os.listdir(path):
#     if file.endswith(".png") or file.endswith(".jpg"):
#         label = file.split(".")[0]
#         labels.append(label)
#         full_file_path = os.path.join(path, file)
#         images.append(full_file_path)
#char_ = sorted(set(char for label in labels for char in label))

char_ = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'a', 'b', 'c', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'n', 'p', 'q', 's', 't', 'u', 'v', 'x', 'y', 'z']

char_to_num = tf.keras.layers.experimental.preprocessing.StringLookup(
    vocabulary=list(char_), num_oov_indices=1,
)
num_to_char = tf.keras.layers.experimental.preprocessing.StringLookup(
    vocabulary=char_to_num.get_vocabulary(), invert=True
)


print(char_)
# Tạo danh sách ký tự từ chuỗi đầu vào
char_ = list(set(char_))

# Chuyển đổi chuỗi thành số
encoded_text = char_to_num(char_)
print(encoded_text)
encoded_text = num_to_char(encoded_text)
print(encoded_text)

def encode_single_sample(img_path, label):
    img = tf.io.read_file(img_path)
    img = tf.io.decode_png(img, channels=1)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = tf.image.resize(img, [img_height, img_width])
    img = tf.transpose(img, perm=[1, 0, 2])
    label = char_to_num(tf.strings.unicode_split(label, input_encoding="UTF-8"))
    # Padding độ dài nhãn để đảm bảo chúng có cùng độ dài
    label = tf.pad(label, [[0, max_length - tf.shape(label)[0]]])
    return {"image": img, "label": label}


def decode_batch_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    # Use greedy search. For complex tasks, you can use beam search
    results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][
        :, :max_length
    ]
    # Iterate over the results and get back the text
    output_text = []
    for res in results:
        res = tf.strings.reduce_join(num_to_char(res)).numpy().decode("utf-8")
        output_text.append(res)
    return output_text

#chia
x_train = images[:58]
y_train = labels[:58]

x_val = images[58:63]
y_val = labels[58:63]

x_test = images[63:70]
y_test = labels[63:70]


batch_size = 20
img_width = 280
img_height = 70
max_length = 6

# train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train))
# train_dataset = (train_dataset.map(encode_single_sample).batch(batch_size))
#
# val_dataset = tf.data.Dataset.from_tensor_slices((x_val, y_val))
# val_dataset = (val_dataset.map(encode_single_sample).batch(batch_size))
#
# test_dataset = tf.data.Dataset.from_tensor_slices((x_test, y_test))
# test_dataset = (test_dataset.map(encode_single_sample).batch(batch_size))

class CTCLayer(layers.Layer):
    def __init__(self, name=None):
        super().__init__(name=name)
        self.loss_fn = keras.backend.ctc_batch_cost


    def call(self, y_true, y_pred):
        # Compute the training-time loss value and add it
        # to the layer using `self.add_loss()`.
        batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
        input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
        label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")

        input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
        label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")

        loss = self.loss_fn(y_true, y_pred, input_length, label_length)
        self.add_loss(loss)

        # At test time, just return the computed predictions
        return y_pred


def build_model():
    input_img = layers.Input(shape=(img_width, img_height, 1), name="image", dtype="float32")
    labels = layers.Input(name="label", shape=(max_length,), dtype="float32")

    # First conv block
    x = layers.Conv2D(
        32,
        (3, 3),
        activation="relu",
        kernel_initializer="he_normal",
        padding="same",
        name="Conv1",
    )(input_img)
    x = layers.MaxPooling2D((2, 2), name="pool1")(x)

    # Second conv block
    x = layers.Conv2D(
        64,
        (3, 3),
        activation="relu",
        kernel_initializer="he_normal",
        padding="same",
        name="Conv2",
    )(x)
    x = layers.MaxPooling2D((2, 2), name="pool2")(x)

    # Thrid conv block
    x = layers.Conv2D(
        128,
        (3, 3),
        activation="relu",
        kernel_initializer="he_normal",
        padding="same",
        name="Conv3",
    )(x)
    x = layers.MaxPooling2D((2, 2), name="pool3")(x)

    new_shape = (35, 8 * 128) # /6 /8 /10 - /128 /56/ /
    x = layers.Reshape(target_shape=new_shape, name="reshape")(x)
    x = layers.Dense(5000, activation="relu", name="dense1")(x)
    x = layers.Dense(3000, activation="relu", name="dense2")(x)
    x = layers.Dense(1000, activation="relu", name="dense3")(x)
    x = layers.Dense(128, activation="relu", name="dense4")(x)
    x = layers.Dropout(0.2)(x)

    # RNNs
    x = layers.Bidirectional(layers.LSTM(256, return_sequences=True, dropout=0.15))(x)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=0.15))(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True, dropout=0.20))(x)

    # Output layer
    x = layers.Dense(len(char_)+1, activation="softmax", name="dense5")(x)
    # Add CTC layer for calculating CTC loss at each step
    output = CTCLayer(name="ctc_loss")(labels, x)


    # Define the model
    model = keras.models.Model(
        inputs=[input_img, labels], outputs=output, name="ocr_model_v1"
    )
    # Optimizer
    opt = keras.optimizers.Adam()
    # Compile the model and return
    model.compile(optimizer=opt)
    return model


# model = build_model()
# model.summary()
# # Đánh giá độ chính xác trên tập kiểm tra
#
# history = model.fit(
#     train_dataset,
#     validation_data=val_dataset,
#     epochs=1
# )
#
# model.save("c_model")

# prediction_model = keras.models.Model(
#     model.get_layer(name="image").input, model.get_layer(name="dense2").output
# )
# prediction_model.summary()
#
# for batch in test_dataset.take(1):
#     batch_images = batch["image"]
#     batch_labels = batch["label"]
#
#     preds = prediction_model.predict(batch_images)
#     pred_texts = decode_batch_predictions(preds)
#
#     orig_texts = []
#     for label in batch_labels:
#         label = tf.strings.reduce_join(num_to_char(label)).numpy().decode("utf-8")
#         orig_texts.append(label)
#     num_samples = len(pred_texts)
#     num_rows = (num_samples - 1) // 4 + 1
#     num_cols = min(num_samples, 4)
#     _, ax = plt.subplots(num_rows, num_cols, figsize=(15, 5))
#
#     for i in range(len(pred_texts)):
#         img = (batch_images[i, :, :, 0] * 255).numpy().astype(np.uint8)
#         img = img.T
#         title = f"Prediction: {pred_texts[i]}"
#         ax[i // num_cols, i % num_cols].imshow(img, cmap="gray")
#         ax[i // num_cols, i % num_cols].set_title(title)
#         ax[i // num_cols, i % num_cols].axis("off")
#     plt.show(
#plt.show()

# from keras.models import load_model
# loaded_model = load_model("c_model.h5", custom_objects={"CTCLayer": CTCLayer})
# def preprocess_image(img_path):
#     img = tf.io.read_file(img_path)
#     img = tf.io.decode_png(img, channels=1)
#     img = tf.image.convert_image_dtype(img, tf.float32)
#     img = tf.image.resize(img, [img_height, img_width])
#     img = tf.transpose(img, perm=[1, 0, 2])
#     return img
# def predict_image(image_path):
#     img = preprocess_image(image_path)
#     img = tf.expand_dims(img, axis=0)
#     prediction = loaded_model.predict([img, np.zeros((1, max_length))])
#     decoded_prediction = decode_batch_predictions(prediction)[0]
#     return decoded_prediction
# image_path = "Net7/a8WpLD.png"
# prediction = predict_image(image_path)
# print(prediction)


# import tensorflow as tf
# import cv2
# import numpy as np
#
# # Tải model đã lưu
# model = tf.keras.models.load_model("saved_models/1/")
#
# # Đường dẫn đến ảnh cần dự đoán
# image_path = "Net7/YHzutf.png"
#
# def preprocess_image(img_path):
#     img = tf.io.read_file(img_path)
#     img = tf.io.decode_png(img, channels=1)
#     img = tf.image.convert_image_dtype(img, tf.float32)
#     img = tf.image.resize(img, [img_height, img_width])
#     img = tf.transpose(img, perm=[1, 0, 2])
#     return img
# def predict_image(image_path):
#     img = preprocess_image(image_path)
#     img = tf.expand_dims(img, axis=0)
#     prediction = model.predict([img, np.zeros((1, max_length))])
#     print(prediction)
#     decoded_prediction = decode_batch_predictions(prediction)[0]
#     return decoded_prediction
#
# image_path = "Net7/a8WpLD.png"
# prediction = predict_image(image_path)
#
# # In kết quả dự đoán
# print("Predicted:", prediction)

























import base64

import cv2
import numpy as np
import grpc

from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc
from tensorflow.core.framework import (
    tensor_pb2,
    tensor_shape_pb2,
    types_pb2
)
#
# import base64
# import tensorflow as tf
# import matplotlib.pyplot as plt
#
# import requests
# import base64
# import json
#
# from keras.datasets.mnist import load_data
# import keras
# from keras import layers
# import base64
# from PIL import Image
#
# import io
#
# def preprocess_base64_image(base64_data):
#     image_data = base64.b64decode(base64_data)
#     image = Image.open(io.BytesIO(image_data))
#     img = image.convert("L")
#     img = img.resize((280, 70))
#     img = np.array(img)
#     img = img.astype(np.float32)/255.0
#     img = tf.convert_to_tensor(img)
#     img = tf.transpose(img, perm=[1, 0])
#     img = tf.expand_dims(img, axis=-1)
#
#     return img
#
# base64_string = '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'
# from tensorflow.python.ops.numpy_ops import np_config
# from keras.preprocessing import image
# def make_prediction(img):
#     url = 'http://localhost:8601/v1/models/solveCaptchas:predict'
#     np_config.enable_numpy_behavior()
#     zeros_array = np.zeros((1, 6))
#     instances = [
#         {
#             "image": img.tolist(),
#             "label": zeros_array.tolist()
#         }
#     ]
#     data = json.dumps({"signature_name": "serving_default", "instances": instances})
#     headers = {'Content-Type': 'application/json'}
#     json_response = requests.post(url, data=data, headers=headers)
#     predictions = json.loads(json_response.text)['predictions']
#     return predictions
# decoded_prediction = decode_batch_predictions(np.array(make_prediction(preprocess_base64_image(base64_string))))[0]
# print(decoded_prediction)
# prediction=make_prediction((preprocess_base64_image(base64_string)))
# decoded_prediction = decode_batch_predictions(prediction)[0]

