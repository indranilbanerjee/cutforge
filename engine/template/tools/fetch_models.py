"""Download the open models the tools use into models/ (once per machine), verified by size and md5.
  yunet  face detection   OpenCV Zoo, MIT            (faces.py, ai_gen.py face guard)
  sface  face recognition OpenCV Zoo, Apache-2.0     (faces.py clustering)
  depth  Depth Anything V2 SMALL, Apache-2.0         (depth.py). Base/Large/Giant are CC-BY-NC: never for client work.
rembg downloads its own u2net weights on first use (Apache-2.0); never use bria-rmbg without a commercial licence.
usage: python tools/fetch_models.py [yunet sface depth]"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, hashlib, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT

M = {
    'yunet': ('https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
              'yunet.onnx', 232589, '4ae92eeb150c82ce15ac80738b3b8167'),
    'sface': ('https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx',
              'sface.onnx', 38696353, '943693ea9c7ddfd9a66dc7b7e8d52a4f'),
    'depth': ('https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model.onnx',
              'depth_v2_small.onnx', 99060839, 'b06a70d234527236bdd08c00827b893d'),
}
D = os.path.join(ROOT, 'models'); os.makedirs(D, exist_ok=True)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def path(name):
    """local path of a model, downloading it if needed"""
    url, fn, size, sig = M[name]; p = os.path.join(D, fn)
    if os.path.exists(p) and os.path.getsize(p) == size: return p
    print(f'downloading {name} ({size / 1e6:.0f} MB) ...', flush=True)
    urllib.request.urlretrieve(url, p + '.part')
    got = md5(p + '.part')
    if got != sig: print(f'  warning: {name} md5 {got} differs from the tested file {sig} (upstream may have changed); check before relying on it')
    os.replace(p + '.part', p); return p


if __name__ == '__main__':
    for n in (sys.argv[1:] or list(M)): print(n, path(n))
