from predict import predict_fn, load_model
import os
import gradio as gr

model_path = os.path.join(os.environ.get("MODEL_DOWNLOAD_PATH", "."), "mnist_model.h5")
model = load_model(model_path)


def get_inference(img_arr):
    return predict_fn(model, img_arr)


interface = gr.Interface(
    fn=get_inference,
    inputs="image",
    outputs="label",
    examples=[["sample_images/0.jpg"], ["sample_images/1.jpg"]],
)

interface.launch(server_name="0.0.0.0", server_port=8000)
