import threading
import time
import cv2
import psutil
from datetime import datetime
import pandas as pd
from queue import Queue

class StreamCaptureManager:
    def __init__(self):
        self.video_benchmark_metrics = self.ini_benchmark_metrics()
        self.ini_params() # Init other detection params

    def ini_benchmark_metrics(self):
        return {
            'timestamps': [],
            'frame_times': [],
            'cpu_usage': [],
            'memory_usage': [],
            'frame_id': []
        }

    def ini_params(self):
        self.visualisation_start_frame = 0
        self.start_time = 0.0
        self.capture_queue = Queue(maxsize=500)
        self.result_queue = Queue(maxsize=500)
        self.total_frame = Queue(maxsize=500)

        self.running = False
        self.video_frame_count_visualized = 0
        self.video_frame_obtained = 0
        self.video_frame_processed = 0

        self.frame_size = (0, 0)
        self.start_time = 0.0
        self.capture_start_time = 0.0
        self.visualisation_time_elapsed = 0.0 # Total time until the visualisation starts
        self.video_fps = 0
        self.stream_fps = 30 # Regulated fps for stream and visualisation : 1 frame every 50ms
        self.stream_noise_time = 2 # Time noise
        self.source = ""
        self.stream_first_frame = None
        self.video_codec = None

    def capture_thread(self, cap : cv2.VideoCapture, flip : bool):
        """
        Thread for getting frame
        """
        frame_id = 0
        print('Debug : Collecting frames')
        while self.running:
            ret, frame = cap.read()

            if not ret:
                break
                
            if frame_id == 10:
                self.stream_first_frame = frame

            frame_id += 1
            self.video_frame_obtained += 1

            if flip:
                frame = cv2.flip(frame, 1)

            sleep_time = 1 / self.video_fps
            time.sleep(0.03333) # 1 frame every 33ms
            
            if not self.capture_queue.full():
                self.capture_queue.put((frame, frame_id))
            if self.capture_queue.full():
                self.capture_queue.get_nowait()
                self.capture_queue.put((frame, frame_id))

    def processing_thread(self, fps):
        """
        Thread for video frame processing
        """
        print('Debug : Processing collected frames')
        while self.running:
            if self.capture_queue.empty():
                continue
            else : 
                if not self.capture_queue.empty():
                    frame, frame_id = self.capture_queue.get()
                    frame_start = time.time()
                    
                    # Starting model detection
                    detection_start_time = time.time()
                    
                    # Saving metrics
                    self.record_metrics(frame_start, frame_id)
                    
                    # Add to result queue
                    if not self.result_queue.full():
                        self.result_queue.put((frame, frame_id))
                        
                    if self.result_queue.full():
                        self.result_queue.get_nowait()

                    if self.total_frame.full():
                        self.total_frame.get_nowait()
                    # self.total_frame.put(drawed_output_frame)

    def start_detection_threads(self, source, flip, save_path):
        """
        Detection process using threads
        """
        self.start_time = time.time()
        cap = cv2.VideoCapture(source)
        self.video_fps = cap.get(cv2.CAP_PROP_FPS)
        self.frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))) # (Width, height)
        self.source = source
        # Camera optimization
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduice the buffer size
        cap.set(cv2.CAP_PROP_FPS, 30)  # Use 30 fps
        
        # Get video Codec
        if type(source) == str:
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            self.video_codec = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])

        # Creation of threads
        capture_thread = threading.Thread(target = self.capture_thread, args=(cap, flip)) # Video Capture thread
        processing_thread = threading.Thread(target = self.processing_thread, args=(self.stream_fps, )) # Processing thread

        # Start threads
        self.running = True
        capture_thread.start()
        processing_thread.start()
        
        try:
            while self.running:
                # Escape
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 28:  # 'q' ou Escape
                    break
                    
                # Real time fps visualization
                if self.video_frame_count_visualized > 0:
                    elapsed_time = time.time() - self.start_time
                    current_fps = self.video_frame_count_visualized / elapsed_time

                # Getting the result
                if self.result_queue.full():
                    self.result_queue.get_nowait()

                if not self.result_queue.empty(): # Frame visualization
                    drawed_frame, frame_id = self.result_queue.get()
                    self.real_time_visualisation(drawed_frame, frame_id)
                    
                # if self.result_queue.empty() and self.capture_queue.empty() and self.video_frame_processed > 1000: # End
                #     print("\nFin traitement")
                #     break
        except KeyboardInterrupt:
            print("\nArrêt demandé par l'utilisateur")
        finally:
            self.stop_threads(capture_thread, processing_thread, cap, save_path)
            print(f"\nNombre total : Traité : {self.video_frame_processed} frames visualisé: {self.video_frame_count_visualized} obtenues de la camera : {self.video_frame_obtained}")

    def get_real_fps(self, frame_count, elapsed_time):
        return int(frame_count / elapsed_time)
    
    def real_time_visualisation(self, drawed_frame, frame_id):
        """
        Real time visualization
        """
        start = time.time()

        if self.video_frame_count_visualized < 1:
            self.visualisation_start_frame = frame_id
            self.start_time = time.time()
        computed_elapsed_time = (frame_id - self.visualisation_start_frame) / self.stream_fps 
        self.visualisation_time_elapsed = 0.0 if computed_elapsed_time - self.stream_noise_time < 0 else computed_elapsed_time - self.stream_noise_time
        # Real time visualisation
        cv2.imshow('Real time detection', drawed_frame)
        self.video_frame_count_visualized += 1
        elapsed = time.time() - start

    def stop_threads(self, capture_thread, processing_thread, cap, save_path):
        """
        Stop all threads and save result video
        """
        # Stop all threads
        self.running = False
        
        # Wait for threads end
        capture_thread.join(timeout=2)
        processing_thread.join(timeout=2)
        
        # Free resources
        cap.release()
        cv2.destroyAllWindows()
        
        # Save the report
        self.save_report()
        # save_video(list(self.total_frame.queue), save_path, 30)


    def record_metrics(self, frame_start, frame_number):
        """
        Record the metric per frame
        """
        # Treatment time
        frame_time = time.time() - frame_start
        fps = 1 / frame_time if frame_time > 0 else 0
        # System Metrics
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        # Save
        self.video_benchmark_metrics['timestamps'].append(datetime.now())
        self.video_benchmark_metrics['frame_times'].append(frame_time)
        self.video_benchmark_metrics['cpu_usage'].append(cpu)
        self.video_benchmark_metrics['memory_usage'].append(memory)
        self.video_benchmark_metrics['frame_id'].append(frame_number)
    
    def save_report(self):
        """
        Calculate the mean of metrics properties
        """
        total_time = time.time() - self.start_time
        df = pd.DataFrame(self.video_benchmark_metrics)
        
        # Mean estimation
        avg_fps = 1 / df['frame_times'].mean()
        avg_cpu = df['cpu_usage'].mean()
        avg_mem = df['memory_usage'].mean()
        
        # Price estimation
        cost_per_hour = 0.50  # $ par heure pour un instance type
        cost_per_minute = (cost_per_hour / 60) * (total_time / 60)
        
        # Saving results
        # with open("benchmark_report.txt", "w") as f:
        #     f.write(f"=== BENCHMARK REPORT ===\n")
        #     f.write(f"Durée totale: {total_time:.2f} secondes\n")
        #     f.write(f"FPS moyen: {avg_fps:.2f}\n")
        #     f.write(f"CPU moyen: {avg_cpu:.2f}%\n")
        #     f.write(f"Mémoire moyenne: {avg_mem:.2f}%\n")
        #     f.write(f"Coût estimé: ${cost_per_minute:.4f}\n")
        #     f.write(f"\nDétails par frame:\n")
        #     df.to_string(f, index=False)
        # df.to_csv("benchmark_data.csv", index=False)
        print("Rapport de benchmark sauvegardé.")