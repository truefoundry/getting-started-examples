from fastapi import FastAPI
from pydantic import BaseModel
from predict import predict_fn, load_model
import tensorflow as tf
import os

model_path = os.path.join(
    os.environ.get("MODEL_DOWNLOAD_PATH", "."), "mnist_model.h5"
)
model = load_model(model_path)


class ImageUrl(BaseModel):
    url: str = "https://conx.readthedocs.io/en/latest/_images/MNIST_6_0.png"


def load_image(img_url):
    img_path = tf.keras.utils.get_file("image.jpg", img_url)
    img = tf.keras.preprocessing.image.load_img(img_path, target_size=(28, 28))
    img_arr = tf.keras.preprocessing.image.img_to_array(img)
    img_arr = tf.image.rgb_to_grayscale(img_arr) / 255.0
    return img_arr 


app = FastAPI()


@app.post("/predict")
async def predict(body: ImageUrl):
    img_arr = load_image(body.url)
    prediction = predict_fn(model, img_arr)
    return {"prediction": prediction}