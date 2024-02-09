import mlfoundry
import tensorflow as tf
from tensorflow.keras.datasets import mnist
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import mnist
import os
import argparse

# parsing the arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--num_epochs", type=int, default=4
)
parser.add_argument(
    "--ml_repo", type=str, required=True
)
args = parser.parse_args()

ML_REPO_NAME=args.ml_repo

# Load the MNIST dataset
(x_train, y_train), (x_test, y_test) = mnist.load_data()

print(f"The number of train images: {len(x_train)}")
print(f"The number of test images: {len(x_test)}")

# Plot some sample images
plt.figure(figsize=(10, 5))
for i in range(10):
    plt.subplot(2, 5, i+1)
    plt.imshow(x_train[i], cmap='gray')
    plt.title(f"Label: {y_train[i]}")
    plt.axis('off')
plt.tight_layout()
plt.show()


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


# Creating client for logging the metadata
client = mlfoundry.get_client()

client.create_ml_repo(args.ml_repo)
run = client.create_run(ml_repo=args.ml_repo)


#logging the parameters
run.log_params({"optimizer": "adam", "loss": "sparse_categorical_crossentropy", "metric": ["accuracy"]})



# Train the model
epochs = args.num_epochs
model.fit(x_train, y_train, epochs=epochs, validation_data=(x_test, y_test))

# Evaluate the model
loss, accuracy = model.evaluate(x_test, y_test)
print(f'Test loss: {loss}')
print(f'Test accuracy: {accuracy}')


# Log Metrics and Model

# Logging the metrics of the model
run.log_metrics(metric_dict={"accuracy": accuracy, "loss": loss})

# Save the trained model
model.save('mnist_model.h5')

# Logging the model
run.log_model(
    name="handwritten-digits-recognition",
    model_file_or_folder='mnist_model.h5',
    framework="tensorflow",
    description="sample model to recognize the handwritten digits",
    metadata={"accuracy": accuracy, "loss": loss},
    step=1,  # step number, useful when using iterative algorithms like SGD
)


