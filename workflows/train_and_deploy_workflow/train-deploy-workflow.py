from typing import Any, Dict, List, Tuple, Union
from truefoundry.workflow import task, workflow, PythonTaskConfig, TaskPythonBuild, map_task, conditional
from truefoundry.deploy import Resources
from functools import partial
import tensorflow as tf
from tensorflow.keras.datasets import mnist
import numpy as np


task_config = PythonTaskConfig(
    image=TaskPythonBuild(
        python_version="3.9",
        pip_packages=["truefoundry[workflow]==0.5.2", "tensorflow==2.15.0", "s3fs>=2024.10.0"],
    ),
    resources=Resources(cpu_request=1.2, cpu_limit=1.2, memory_limit=3000, memory_request=3000, ephemeral_storage_limit=2000, ephemeral_storage_request=2000),
    service_account="default",
    env={
        "TF_CPP_MIN_LOG_LEVEL": "3", # suppress tensorflow warnings
        "FLYTE_SDK_LOGGING_LEVEL": "40",
        "TFY_API_KEY": "<your-api-key>",
        "TFY_HOST": "<tfy-host-value>", 
        }
)


@task(task_config=task_config)
def fetch_data() -> Dict[str, np.array]:
    (x_train, y_train), (x_test, y_test)  = mnist.load_data()
    return {
        "x_train": x_train,
        "y_train": y_train,
        "x_test": x_test,
        "y_test": y_test
    }


@task(task_config=task_config)
def train_model(epochs: int, learning_rate: float, data: Dict[str, np.array], ml_repo:str) -> str:
    from truefoundry.ml import get_client

    x_train, y_train, x_test, y_test = data["x_train"], data["y_train"], data["x_test"], data["y_test"]
    x_train = x_train / 255.0
    x_test = x_test / 255.0

    client = get_client()
    run = client.create_run(ml_repo=ml_repo)

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dense(10, activation="softmax"),
        ]
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    # Compile the model
    model.compile(optimizer=optimizer, loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    epochs = epochs
    print(f"Started training the model for {epochs} epochs")
    history = model.fit(x_train, y_train, epochs=epochs, validation_data=(x_test, y_test))

    # Evaluate the model
    loss, accuracy = model.evaluate(x_test, y_test)
    print(f"Test loss: {loss}")
    print(f"Test accuracy: {accuracy}")

    history_dict = history.history
    train_accuracy = history_dict['accuracy']
    val_accuracy = history_dict['val_accuracy'] 
    loss = history_dict['loss']  

    for epoch in range(epochs):
        run.log_metrics({"train_accuracy": train_accuracy[epoch], "val_accuracy": val_accuracy[epoch], "loss": loss[epoch]}, step=epoch+5)
    
    model.save("mnist_model.h5")

    run.log_model(
        name="handwritten-digits-recognition",
        model_file_or_folder="mnist_model.h5",
        framework="tensorflow",
        description="sample model to recognize the handwritten digits",
        metadata={"accuracy": accuracy, "loss": loss},
        step=1,
    )

    run_fqn = run.fqn
    run.end()
    return run_fqn

@task(task_config=task_config)
def get_run_fqn_of_best_model(fqns: List[str], threshold: float) -> Tuple[str, bool]:
    from truefoundry.ml import get_client
    client = get_client()
    curr_accuracy = 0
    best_fqn = None
    print(f"Finding the best models from {len(fqns)} models")
    for fqn_no in range(len(fqns)):
        print(f"Comparing accuracy for model {fqn_no+1}")
        run = client.get_run_by_fqn(fqns[fqn_no])
        accuracy_metric = run.get_metrics().get("val_accuracy", 0)
        accuracy = accuracy_metric[-1].value
        if accuracy > curr_accuracy and accuracy > threshold:
            curr_accuracy = accuracy
            best_fqn = fqns[fqn_no]
    if best_fqn:
        print("The fqn of the best model is: ", best_fqn)
        return best_fqn, True
    print("No model found with accuracy greater than threshold")
    return '', False

@task(task_config=task_config)
def deploy_model(run_fqn: str, workspace_fqn: str) -> str:
    from truefoundry.ml import get_client
    from deploy_model.deploy import deploy_service

    client = get_client()
    run = client.get_run_by_fqn(run_fqn)
    models = run.list_model_versions()
    model = models.__next__()
    print(f"Deploying model {model.fqn}")
    url = deploy_service(model_version_fqn=model.fqn, workspace_fqn=workspace_fqn)
    return f"Model deployed at {url}"

@task(task_config=task_config)
def model_not_found(threshold: float) -> str:
    return f"Model with threshold greater than {threshold} not found"


@workflow
def model_training_workflow(ml_repo: str, workspace_fqn: str, epochs: List[int] = [2, 3, 5], learning_rate: List[float] = [0.1, 0.001, 0.001], accuracy_threshold: float = 0.15) -> Union[str, None]:
    data = fetch_data()
    train_model_function = partial(train_model, data=data, ml_repo=ml_repo)
    fqns = map_task(train_model_function, concurrency=2)(epochs=epochs, learning_rate=learning_rate)
    model_version_fqn, does_model_pass_threshold_accuracy = get_run_fqn_of_best_model(fqns=fqns, threshold=accuracy_threshold)
    message = conditional("Deploy model").if_(does_model_pass_threshold_accuracy == True).then(deploy_model(run_fqn=model_version_fqn, workspace_fqn=workspace_fqn)).else_().then(model_not_found(threshold=accuracy_threshold))

    return message