# We need to prepare image for processing,
# so func will return bytes (????)
import io

import torch
import torchvision.transforms as transform
from torchvision import models
from PIL import Image


def get_model(path=None):
    if None not in path:
        model = torch.load(path)
    else:
        model = models.densenet121(pretrained=True)
    model.eval()
    return model


def transform_image(image_bytes):
    my_transform = transform.Compose([
        transform.Resize(255),
        transform.CenterCrop(224),
        transform.ToTensor(),
        transform.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225])])
    image = Image.open(io.BytesIO(image_bytes))
    return my_transform(image).unsqueeze(0)


def format_class_name(class_name):
    class_name = class_name.replace('_', ' ')
    class_name = class_name.title()
    return class_name
