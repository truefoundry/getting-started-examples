import os

import gradio as gr
from predict import load_model, predict_fn

model_path = os.path.join(os.environ.get("MODEL_DOWNLOAD_PATH", "."), "mnist_model.h5")
model = load_model(model_path)


def get_inference(img_arr):
    return predict_fn(model, img_arr)


interface = gr.Interface(
    fn=get_inference,
    inputs="image",
    outputs="label",
    examples=[
        ["sample_images/3.jpg"],
        ["sample_images/8.jpg"],
        ["sample_images/7.png"],
    ],
)
interface.launch(
    server_name="0.0.0.0",
    server_port=8000,
    root_path=os.environ.get("TFY_SERVICE_ROOT_PATH"),
)
