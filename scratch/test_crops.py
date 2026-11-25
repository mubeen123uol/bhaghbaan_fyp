import os
from PIL import Image

def smart_crop_center(img, target_size=(1200, 900)):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    w, h = img.size
    target_w, target_h = target_size
    target_aspect = target_w / target_h
    current_aspect = w / h
    
    if current_aspect > target_aspect:
        crop_w = int(h * target_aspect)
        left = (w - crop_w) // 2
        img = img.crop((left, 0, left + crop_w, h))
    else:
        crop_h = int(w / target_aspect)
        top = int((h - crop_h) * 0.4)
        img = img.crop((0, top, w, top + crop_h))
        
    return img.resize(target_size, Image.Resampling.LANCZOS)

# Check sheesham_leaves
if os.path.exists('scratch/tree_cands/sheesham_leaves.jpg'):
    im = Image.open('scratch/tree_cands/sheesham_leaves.jpg')
    print('sheesham_leaves size:', im.size)
    cropped = smart_crop_center(im)
    cropped.save('scratch/test_sheesham_leaves_crop.jpg', quality=92)
    print('Saved scratch/test_sheesham_leaves_crop.jpg')

# Check sheesham_tree
if os.path.exists('scratch/tree_cands/sheesham_tree.jpg'):
    im = Image.open('scratch/tree_cands/sheesham_tree.jpg')
    print('sheesham_tree size:', im.size)
    cropped = smart_crop_center(im)
    cropped.save('scratch/test_sheesham_tree_crop.jpg', quality=92)
    print('Saved scratch/test_sheesham_tree_crop.jpg')

# Check neem_tree_punjab
if os.path.exists('scratch/tree_cands/neem_tree_punjab.jpg'):
    im = Image.open('scratch/tree_cands/neem_tree_punjab.jpg')
    print('neem_tree_punjab size:', im.size)
    cropped = smart_crop_center(im)
    cropped.save('scratch/test_neem_tree_punjab_crop.jpg', quality=92)
    print('Saved scratch/test_neem_tree_punjab_crop.jpg')
