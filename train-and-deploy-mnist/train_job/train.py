import argparse

import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.datasets import mnist
from truefoundry.ml import get_client

# parsing the arguments
parser = argparse.ArgumentParser()
parser.add_argument("--num_epochs", type=int, default=4)
parser.add_argument("--learning_rate", type=float, default=0.01)
parser.add_argument(
    "--ml_repo",
    type=str,
    required=True,
    help="""\
        The name of the ML Repo to track metrics and models.
        You can create one from the ML Repos Tab on the UI.
        Docs: https://docs.truefoundry.com/docs/key-concepts#creating-an-ml-repo",
    """,
)
args = parser.parse_args()


# Load the MNIST dataset
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Normalize the pixel values between 0 and 1
x_train = x_train / 255.0
x_test = x_test / 255.0

print(f"The number of train images: {len(x_train)}")
print(f"The number of test images: {len(x_test)}")

# Creating client for logging the metadata
client = get_client()

run = client.create_run(ml_repo=args.ml_repo, run_name="train-model")

# Plot some sample images
plt.figure(figsize=(10, 5))
for i in range(10):
    plt.subplot(2, 5, i + 1)
    plt.imshow(x_train[i], cmap="gray")
    plt.title(f"Label: {y_train[i]}")
    plt.axis("off")
run.log_plots({"images": plt})
plt.tight_layout()


# Define the model architecture
model = tf.keras.Sequential(
    [
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(10, activation="softmax"),
    ]
)

optimizer = tf.keras.optimizers.Adam(learning_rate=args.learning_rate)
# Compile the model
model.compile(optimizer=optimizer, loss="sparse_categorical_crossentropy", metrics=["accuracy"])

# logging the parameters
run.log_params(
    {
        "optimizer": "adam",
        "loss": "sparse_categorical_crossentropy",
        "metric": ["accuracy"],
    }
)

# Train the model
epochs = args.num_epochs
history = model.fit(x_train, y_train, epochs=epochs, validation_data=(x_test, y_test))

# Evaluate the model
loss, accuracy = model.evaluate(x_test, y_test)
print(f"Test loss: {loss}")
print(f"Test accuracy: {accuracy}")

history_dict = history.history
train_accuracy = history_dict['accuracy']  # Training accuracy per epoch
val_accuracy = history_dict['val_accuracy'] 
loss = history_dict['loss']  # Training loss per epoch  

# Log Metrics and Model

# Logging the metrics of the model
for epoch in range(epochs):
    run.log_metrics({"train_accuracy": train_accuracy[epoch], "val_accuracy": val_accuracy[epoch], "loss": loss[epoch]}, step=epoch+5)

# Save the trained model
model.save("mnist_model.h5")

# Logging the model
run.log_model(
    name="handwritten-digits-recognition",
    model_file_or_folder="mnist_model.h5",
    framework="tensorflow",
    description="sample model to recognize the handwritten digits",
    metadata={"accuracy": accuracy, "loss": loss},
    step=1,  # step number, useful when using iterative algorithms like SGD
)
