import cv2

class DrawManager:

    def __init__(self):
        pass

    def draw_general_infos(self, frame, frame_size, video_fps, time_elapsed):
        """
        Draw a recangle which contains the number of fps and the number of persons detected
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2
        alpha = 0.8

        fps_label = f"fps : {round(video_fps)}"
        elapsed_time_label = f"tps : {time_elapsed:.3f} scs"
        frame_width = frame_size[0]
        frame_height = frame_size[1]
        rect_width = int(frame_width * 0.6)
        rect_hight = int(frame_height * 0.1)

        fps_label_x, fps_label_y = 20, 20
        time_x, time_y = fps_label_x + self._get_label_width(fps_label, font, font_scale, thickness) + 10, fps_label_y 

        text_color = (0, 0, 255)  
        box_color = (235, 206, 135)

        self.draw_top_labels(frame, fps_label, fps_label_x, fps_label_y, text_color, font, font_scale, thickness)
        self.draw_top_labels(frame, elapsed_time_label, time_x, time_y, text_color, font, font_scale, thickness)

        # Drawing the container rectangle
        overlay = frame.copy() # Copy the frame
        cv2.rectangle(
            frame,
            (0, 0),
            (rect_width, rect_hight),
            box_color,
            thickness=-1
        )
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame) # Add overlay frame the the real frame

        return frame



    def _get_label_width(self, label, font, font_scale, thickness):
        (text_width, text_height), _ = cv2.getTextSize(
        label, font, font_scale, thickness)
        return text_width

    
    def draw_top_labels(self, frame, fps_label, fps_label_x, fps_label_y, text_color, font, fontscale, thickness):
        # Writing the fps
        cv2.putText(
            frame,
            fps_label,
            (fps_label_x, fps_label_y),
            font,
            fontscale,
            text_color,
            thickness
        )

    def draw_land_skels():
        pass
