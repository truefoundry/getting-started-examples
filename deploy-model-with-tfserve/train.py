import tensorflow as tf
from tensorflow import keras

# Helper libraries
import os


mnist = keras.datasets.mnist
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()

# scale the values to 0.0 to 1.0
train_images = train_images / 255.0
test_images = test_images / 255.0

# reshape for feeding into the model
train_images = train_images.reshape(train_images.shape[0], 28, 28, 1)
test_images = test_images.reshape(test_images.shape[0], 28, 28, 1)

class_names = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

print("\ntrain_images.shape: {}, of {}".format(train_images.shape, train_images.dtype))
print("test_images.shape: {}, of {}".format(test_images.shape, test_images.dtype))

model = keras.Sequential(
    [
        keras.layers.Conv2D(
            input_shape=(28, 28, 1),
            filters=8,
            kernel_size=3,
            strides=2,
            activation="relu",
            name="Conv1",
        ),
        keras.layers.Flatten(),
        keras.layers.Dense(10, name="Dense"),
        keras.layers.Softmax(name="Softmax"),
    ]
)
model.summary()

testing = False
epochs = 5

model.compile(
    optimizer="adam",
    loss=tf.keras.losses.SparseCategoricalCrossentropy(),
    metrics=[keras.metrics.SparseCategoricalAccuracy()],
)
model.fit(train_images, train_labels, epochs=epochs)

test_loss, test_acc = model.evaluate(test_images, test_labels)
print("\nTest accuracy: {}".format(test_acc))


version = 1
export_path = os.path.join("./models", "mnist", str(version))
print("export_path = {}\n".format(export_path))
model.export(export_path)
print("\nSaved model to", export_path)
