import cv2
from pygrabber.dshow_graph import FilterGraph

def find_cameras():
    graph = FilterGraph()
    devices = graph.get_input_devices()
    return devices

if __name__ == "__main__":
    camera_names = find_cameras()
    if not camera_names:
        print("No cameras found.")
    else:
        print("Available cameras:")
        for i, name in enumerate(camera_names):
            print(f"- Index {i}: {name}")
