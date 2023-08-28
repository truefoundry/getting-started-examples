import numpy as np  
from PIL import Image
from tensorflow.keras.datasets import mnist

# Load MNIST dataset

(_, _), (x_test, y_test) = mnist.load_data()

# Find the indices of images with label 0 and 1

zero_indices = np.where(y_test == 0)[0]  
one_indices = np.where(y_test == 1)[0]

# Convert the images to PIL format and save as 0.jpg and 1.jpg

Image.fromarray(x_test[zero_indices[0]]).save("0.jpg")  
Image.fromarray(x_test[one_indices[0]]).save("1.jpg")