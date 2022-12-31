import io
import base64
import torch.cuda
from PIL import Image
from io import BytesIO
from matplotlib.figure import Figure

from application import app
from application.image_segmentation import print_detectron2_visualization, print_panoptic_segmentation, print_remaining_masks
from flask import render_template, request, jsonify, redirect

from application.inference import get_prediction, get_segmentation
from application.transform_pipeline import format_class_name


@app.route('/about')
def about():
    return render_template("about.html", about=True)


# @app.route('/test', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         if 'file' not in request.files:
#             return redirect(request.url)
#         file = request.files.get('file')
#         if not file:
#             return redirect(request.url)
#         img_bytes = file.read()
#         class_id, class_name = get_prediction(image_bytes=img_bytes)
#         class_name = format_class_name(class_name)
#         return render_template('result.html', class_id=class_id,
#                                class_name=class_name, image_after=img_bytes, is_cuda_used=torch.cuda.is_available())
#     return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def panoptic_image_segmentation():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return redirect(request.url)
        img_bytes = file.read()
        out, result = get_segmentation(image_bytes=img_bytes)
        data2 = print_panoptic_segmentation(result)
        data3 = print_detectron2_visualization(
            result, im=Image.open(io.BytesIO(img_bytes)))
        return render_template('result.html', panoptic=data2, detectron=data3, is_cuda_used=torch.cuda.is_available())
    return render_template('index.html')
