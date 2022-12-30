import base64
import io
import cv2
import math
import numpy
import torch
import requests
import itertools
import panopticapi
from torch import nn
from PIL import Image
import seaborn as sns
import IPython.display
from copy import deepcopy
import matplotlib.pyplot as plt
from detectron2.config import get_cfg
from torchvision.models import resnet50
import torchvision.transforms as transform
from detectron2.data import MetadataCatalog
from panopticapi.utils import id2rgb, rgb2id
from detectron2.utils.visualizer import Visualizer

# torch.set_grad_enabled(False)

# model, postprocessor = torch.hub.load('facebookresearch/detr', 'detr_resnet101_panoptic', pretrained=True,
#                                       return_postprocessor=True, num_classes=250)


# def get_model():
#     return model.to(torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')).eval()


# def read_coco_classes_from_file(path='application/static/coco_classes.txt'):
#     coco_classes_file = open(path, "r")

#     coco_classes = coco_classes_file.read()
#     coco_classes_file.close()
#     return coco_classes.split(",")


# Detectron2 uses a different numbering scheme, we build a conversion table
# def conversion_table(CLASSES):
#     coco2d2 = {}
#     count = 0
#     for i, c in enumerate(CLASSES):
#         if c != "N/A":
#             coco2d2[i] = count
#             count += 1


# coco2d2 = conversion_table(read_coco_classes_from_file())


# standard PyTorch mean-std input image normalization
# def transform_image(image_bytes):
#     transform = transform.Compose([
#         transform.Resize(800),
#         transform.ToTensor(),
#         transform.Normalize(
#             [0.485, 0.456, 0.406],
#             [0.229, 0.224, 0.225])
#     ])
#     image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
#     tensor = transform(image).unsqueeze(0)

#     if torch.cuda.is_available():
#         tensor = tensor.to(torch.device("cuda:0"))
#     return model(tensor)


# compute the scores, excluding the "no-object" class (the last one)
def print_remaining_masks(out):
    buf = io.BytesIO()
    # compute the scores, excluding the "no-object" class (the last one)
    scores = torch.Tensor.cpu(
        out["pred_logits"]).softmax(-1)[..., :-1].max(-1)[0]
    # threshold the confidence
    keep = scores > 0.85

    # Plot all the remaining masks
    ncols = 5
    fig, axs = plt.subplots(ncols=ncols, nrows=math.ceil(
        keep.sum().item() / ncols), figsize=(18, 10))
    for line in axs:
        for a in line:
            a.axis('off')
    for i, mask in enumerate(torch.Tensor.cpu(out["pred_masks"])[keep]):
        ax = axs[i // ncols, i % ncols]
        ax.imshow(mask, cmap="cividis")
        ax.axis('off')
    fig.tight_layout()
    buf.seek(0)
    return Image.open(buf)


# result = postprocessor(out, torch.as_tensor(tensor.shape[-2:]).unsqueeze(0))[0]
def print_panoptic_segmentation(result):
    buf = io.BytesIO()
    palette = itertools.cycle(sns.color_palette())

    # The segmentation is stored in a special-format png
    panoptic_seg = Image.open(io.BytesIO(result['png_string']))
    panoptic_seg = numpy.array(panoptic_seg, dtype=numpy.uint8).copy()
    # We retrieve the ids corresponding to each mask
    panoptic_seg_id = rgb2id(panoptic_seg)

    # Finally we color each mask individually
    panoptic_seg[:, :, :] = 0
    for ID in range(panoptic_seg_id.max() + 1):
        panoptic_seg[panoptic_seg_id == ID] = numpy.asarray(
            next(palette)) * 255
    plt.figure(figsize=(15, 15))
    plt.imshow(panoptic_seg)
    plt.axis('on')
    plt.savefig(buf, format="png")

    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("ascii")
    return data


# result = postprocessor(out, torch.as_tensor(tensor.shape[-2:]).unsqueeze(0))[0]
def print_detectron2_visualization(result):
    # We extract the segments info and the panoptic result from DETR's prediction
    segments_info = deepcopy(result["segments_info"])
    # Panoptic predictions are stored in a special format png
    panoptic_seg = Image.open(io.BytesIO(result['png_string']))
    final_w, final_h = panoptic_seg.size
    # We convert the png into an segment id map
    panoptic_seg = numpy.array(panoptic_seg, dtype=numpy.uint8)
    panoptic_seg = torch.from_numpy(rgb2id(panoptic_seg))

    # Detectron2 uses a different numbering of coco classes, here we convert the class ids accordingly
    meta = MetadataCatalog.get("coco_2017_val_panoptic_separated")
    for i in range(len(segments_info)):
        c = segments_info[i]["category_id"]
        segments_info[i]["category_id"] = meta.thing_dataset_id_to_contiguous_id[
            c] if segments_info[i]["isthing"] else meta.stuff_dataset_id_to_contiguous_id[c]

    # Finally we visualize the prediction
    v = Visualizer(numpy.array(im.copy().resize((final_w, final_h)))
                   [:, :, ::-1], meta, scale=1.0)
    v._default_font_size = 20
    v = v.draw_panoptic_seg_predictions(
        panoptic_seg, segments_info, area_threshold=0)
    return IPython.display(Image.fromarray(cv2.cvtColor(v.get_image(), cv2.COLOR_BGR2RGB)))
