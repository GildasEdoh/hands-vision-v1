from handvision.vision import StreamCaptureManager

def main():
    # Stream Capture
    stream_cap = StreamCaptureManager() # Stream Manager Instance
    stream_cap.start_detection_threads(source=0, flip=True, save_path='save_path.mp4')

if __name__ == '__main__':
    main()