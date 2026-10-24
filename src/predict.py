import json
import numpy as np
from PIL import Image


try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    from tensorflow.lite import Interpreter

MODEL_PATH = "model/disease_model.tflite"
CLASSES_PATH = "model/class_names.json"

CLASS_NAMES = json.load(open(CLASSES_PATH))

interpreter = Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()


def predict(image: Image.Image):
    img = image.convert("RGB").resize((224, 224))
    # raw 0-255 pixel values: the model rescales internally, so do NOT divide by 255
    arr = np.expand_dims(np.array(img, dtype=np.float32), axis=0)

    interpreter.set_tensor(input_details[0]["index"], arr)
    interpreter.invoke()
    probs = interpreter.get_tensor(output_details[0]["index"])[0]

    idx = int(np.argmax(probs))
    return CLASS_NAMES[idx], float(probs[idx])