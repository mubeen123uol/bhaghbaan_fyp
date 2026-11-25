import os
from PIL import Image, ImageStat

files = [
    'scratch/tree_cands/sheesham_leaves.jpg',
    'scratch/tree_cands/sheesham_tree.jpg',
    'scratch/tree_cands/sheesham_nepal.jpg',
    'scratch/tree_cands/neem_tree_punjab.jpg',
    'media/plants/plant_40_dalbergia_sissoo_LsoowOT.jpg',
    'media/plants/plant_37_azadirachta_indica_ESpykqh.jpg'
]

for f in files:
    if os.path.exists(f):
        im = Image.open(f)
        stat = ImageStat.Stat(im)
        print(f"File: {f}")
        print(f"  Size: {im.size}")
        print(f"  Mean RGB: {stat.mean[:3]}")
        # check aspect ratio
        print(f"  Aspect: {im.size[0] / im.size[1]:.2f}")
