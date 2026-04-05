import urllib.request
import os

# NASA Blue Marble - proper Earth texture
url = 'https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57752/land_shallow_topo_2048.jpg'
path = 'C:/Monica/earth_texture_cache.jpg'

print('Downloading NASA Blue Marble texture...')
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response, open(path, 'wb') as out_file:
    out_file.write(response.read())
print(f'Done: {os.path.getsize(path)} bytes')

# Verify colors
import cv2
img = cv2.imread(path)
print(f'Shape: {img.shape}')
print(f'Ocean (should be blue): {img[512, 400]}')
print(f'Africa (should be green/brown): {img[400, 1100]}')
