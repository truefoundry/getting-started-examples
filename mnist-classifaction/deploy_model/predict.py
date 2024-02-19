import tensorflow as tf
import numpy as np


def load_model(model_path: str) -> tf.keras.Model:
    # Load the trained model
    model = tf.keras.models.load_model(model_path)
    return model


def predict_fn(model, img_arr: np.ndarray) -> str:
    # Preprocess the image before passing it to the model
    img_arr = tf.expand_dims(img_arr, 0)
    img_arr = img_arr[:, :, :, 0]  # Keep only the first channel (grayscale)

    # Make predictions
    predictions = model.predict(img_arr)
    predicted_label = tf.argmax(predictions[0]).numpy()

    return str(predicted_label)
