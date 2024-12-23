# from tensorflow.keras.datasets import mnist
# import matplotlib.pyplot as plt
import numpy as np
from tensorflow.keras.datasets import mnist
from PIL import Image

# (x_train, y_train), (x_test, y_test)  = mnist.load_data()

# plt.figure(figsize=(6, 3))

# # First image
# # plt.subplot(1, 2, 1)
# plt.imshow(x_train[0], cmap='gray')
# plt.title(f'Label: {y_train[0]}')

# # Second image
# # plt.subplot(1, 2, 2)
# # plt.imshow(x_train[1], cmap='gray')
# # plt.title(f'Label: {y_train[1]}')

# # Save the figure to a file
# plt.tight_layout()
# plt.savefig('mnist_images.png')

saved_image = Image.open('mnist_images.png')

# Convert the image to a numpy array
saved_image_array = np.array(saved_image)

# Print the pixel values of the saved image
print("\nPixel values of the saved image:")
print(len(saved_image_array[0]))