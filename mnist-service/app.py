import gradio as gr  
import tensorflow as tf  
import numpy as np  
from PIL import Image

def predict(img_arr):
	# Preprocess the image before passing it to the model
  img_arr = tf.expand_dims(img_arr, 0)  
  img_arr = img_arr[:, :, :, 0]  # Keep only the first channel (grayscale)

	# Load the trained model
  loaded_model = tf.keras.models.load_model('mnist_model.h5')

	# Make predictions
  predictions = loaded_model.predict(img_arr)  
  predicted_label = tf.argmax(predictions[0]).numpy()

  return str(predicted_label)

# Setup the gradio interface
gr.Interface(fn=predict,  
             inputs="image",  
             outputs="label",  
             examples=[["0.jpg"], ["1.jpg"]]  
).launch(server_name="0.0.0.0", server_port=8080)