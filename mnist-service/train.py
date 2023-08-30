import tensorflow as tf
from tensorflow.keras.datasets import mnist

# Load the MNIST dataset

(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Normalize the pixel values between 0 and 1

x_train = x_train / 255.0  
x_test = x_test / 255.0

# Define the model architecture

model = tf.keras.Sequential([  
    tf.keras.layers.Flatten(input_shape=(28, 28)),  
    tf.keras.layers.Dense(128, activation='relu'),  
    tf.keras.layers.Dense(10, activation='softmax')  
])

# Compile the model

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Train the model

epochs = 5  
model.fit(x_train, y_train, epochs=epochs, validation_data=(x_test, y_test))

# Evaluate the model

loss, accuracy = model.evaluate(x_test, y_test)  
print(f'Test loss: {loss}')  
print(f'Test accuracy: {accuracy}')

# Save the trained model

model.save('mnist_model.h5')  