"""Straighten a photo of a framed picture or document shot at an angle (ancestor portraits on a wall, certificates,
letters): four-point perspective correction to a flat, upright rectangle.
usage: python tools/vfx/straighten.py photo.jpg out.jpg                      auto: finds the biggest 4-sided outline
       python tools/vfx/straighten.py photo.jpg out.jpg x1,y1 x2,y2 x3,y3 x4,y4   manual corners (any order)
Check the result by eye; with glare or busy frames, give the corners manually."""
import sys, numpy as np, cv2
from PIL import Image, ImageOps


def order(pts):
    pts = np.array(pts, np.float32); s = pts.sum(1); d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)


def auto_quad(img):
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    e = cv2.dilate(cv2.Canny(g, 40, 120), np.ones((3, 3), np.uint8))
    cs, _ = cv2.findContours(e, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    A = img.shape[0] * img.shape[1]
    for c in sorted(cs, key=cv2.contourArea, reverse=True)[:20]:
        ap = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(ap) == 4 and cv2.contourArea(ap) > 0.15 * A: return ap.reshape(4, 2)
    return None


if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    img = cv2.cvtColor(np.array(ImageOps.exif_transpose(Image.open(sys.argv[1])).convert('RGB')), cv2.COLOR_RGB2BGR)
    q = [tuple(map(float, p.split(','))) for p in sys.argv[3:7]] if len(sys.argv) >= 7 else auto_quad(img)
    if q is None: sys.exit('no clear 4-sided outline found: pass the four corners by hand')
    tl, tr, br, bl = order(q)
    w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))); h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    M = cv2.getPerspectiveTransform(np.array([tl, tr, br, bl]), np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32))
    cv2.imwrite(sys.argv[2], cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_CUBIC), [cv2.IMWRITE_JPEG_QUALITY, 94])
    print('straightened', sys.argv[2], f'{w}x{h}')
