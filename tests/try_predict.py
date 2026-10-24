from PIL import Image
from src.predict import predict

disease, confidence = predict(Image.open("test_leaf.jpg"))
print(disease, round(confidence, 3))