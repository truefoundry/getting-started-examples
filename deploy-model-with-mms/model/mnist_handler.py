import io
import json
import os

import numpy as np
import torch
import torch.nn.functional as F
from mnist import Net
from PIL import Image
from torch.autograd import Variable
from torchvision import transforms


class PyTorchImageClassifier:
    """
    PyTorchImageClassifier service class. This service takes a flower
    image and returns the name of that flower.
    """

    def __init__(self):
        self.checkpoint_file_path = None
        self.model = None
        self.mapping = None
        self.device = "cpu"
        self.initialized = False

    def initialize(self, context):
        """
        Load the model and mapping file to perform infernece.
        """

        properties = context.system_properties
        model_dir = properties.get("model_dir")

        # Read checkpoint file
        checkpoint_file_path = os.path.join(model_dir, "mnist_cnn.pt")
        if not os.path.isfile(checkpoint_file_path):
            raise RuntimeError("Missing model.pth file.")

        model = Net()
        state_dict = torch.load(checkpoint_file_path, map_location="cpu")
        model.load_state_dict(state_dict)

        for param in model.parameters():
            param.requires_grad = False

        self.model = model

        # Read the mapping file, index to flower
        mapping_file_path = os.path.join(model_dir, "index_to_name.json")
        if not os.path.isfile(mapping_file_path):
            raise RuntimeError("Missing the mapping file")
        with open(mapping_file_path) as f:
            self.mapping = json.load(f)

        self.initialized = True

    def preprocess(self, data):
        """
        Scales, crops, and normalizes a PIL image for a PyTorch model,
        returns an Numpy array
        """
        image = data[0].get("data")
        if image is None:
            image = data[0].get("body")

        my_preprocess = transforms.Compose(
            [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
        )
        image = Image.open(io.BytesIO(image))
        image = my_preprocess(image)
        return image

    def inference(self, img, topk=10):
        """Predict the class (or classes) of an image using a trained deep learning model."""
        # Convert 2D image to 1D vector
        img = np.expand_dims(img, 0)

        img = torch.from_numpy(img)

        self.model.eval()
        inputs = Variable(img).to(self.device)
        logits = self.model.forward(inputs)

        ps = F.softmax(logits, dim=1)
        topk = ps.cpu().topk(topk)

        probs, classes = (e.data.numpy().squeeze().tolist() for e in topk)

        results = []
        for i in range(len(probs)):
            tmp = dict()
            tmp[self.mapping[str(classes[i])]] = probs[i]
            results.append(tmp)
        return [results]

    def postprocess(self, inference_output):
        return inference_output


# Following code is not necessary if your service class contains `handle(self, data, context)` function
_service = PyTorchImageClassifier()


def handle(data, context):
    if not _service.initialized:
        _service.initialize(context)

    if data is None:
        return None

    data = _service.preprocess(data)
    data = _service.inference(data)
    data = _service.postprocess(data)

    return data
