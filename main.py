import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from datetime import datetime
from hik_camera import HikCamera
from yolo_detector import YoloDetector
from database import DatabaseManager

class HikCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hikvision Area Camera Control")
        self.root.geometry("1200x900")
        self.root.minsize(1000, 700)

        self.db = DatabaseManager()
        
        self.hik_camera = HikCamera()
        self.yolo_detector = YoloDetector()

        self.camera_connected = False
        self.stop_display = False
        self.trigger_mode = False  # New flag for trigger mode
        self.current_trigger_image = None  # Store the trigger-captured image

        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill=tk.BOTH, expand=True)

        self.camera_tab = ttk.Frame(self.main_notebook)
        self.logs_tab = ttk.Frame(self.main_notebook)
        self.stats_tab = ttk.Frame(self.main_notebook)
        
        self.main_notebook.add(self.camera_tab, text="Camera Control")
        self.main_notebook.add(self.logs_tab, text="Logs")
        self.main_notebook.add(self.stats_tab, text="Statistics")

        self.init_camera_tab()
        self.init_logs_tab()
        self.init_stats_tab()

        self.db.add_log("Application started", level="INFO", source="app")

    def init_camera_tab(self):
        self.control_frame = ttk.Frame(self.camera_tab)
        self.control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(self.control_frame, text="Enum Cameras", command=self.enum_cameras).pack(side=tk.LEFT, padx=5)

        self.camera_var = tk.StringVar()
        self.camera_combobox = ttk.Combobox(self.control_frame, textvariable=self.camera_var, state="readonly", width=30)
        self.camera_combobox.pack(side=tk.LEFT, padx=5)

        self.connect_button = ttk.Button(self.control_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(self.control_frame, text="Load Image", command=self.load_local_image).pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="Not Connected")
        self.status_label = ttk.Label(self.control_frame, textvariable=self.status_var, foreground="red")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        self.image_container = ttk.Frame(self.camera_tab)
        self.image_container.pack(fill=tk.BOTH, expand=True, pady=5)

        self.image_frame = ttk.LabelFrame(self.image_container, text="Original Image", padding="5")
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.canvas = tk.Canvas(self.image_frame, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind('<Configure>', self.on_canvas_resize)

        self.detection_frame = ttk.LabelFrame(self.image_container, text="YOLO Detection Result (Person Detection)", padding="5")
        self.detection_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.detection_canvas = tk.Canvas(self.detection_frame, bg='black', highlightthickness=0)
        self.detection_canvas.pack(fill=tk.BOTH, expand=True)

        self.detection_canvas.bind('<Configure>', self.on_detection_canvas_resize)

        self.param_frame = ttk.LabelFrame(self.camera_tab, text="Camera Parameters", padding="10")
        self.param_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.param_frame, text="Exposure(ms):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.exposure_var = tk.DoubleVar(value=10.0)
        ttk.Entry(self.param_frame, textvariable=self.exposure_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.param_frame, text="Set", command=self.set_exposure).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.param_frame, text="Gain(dB):").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.gain_var = tk.DoubleVar(value=0.0)
        ttk.Entry(self.param_frame, textvariable=self.gain_var, width=10).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(self.param_frame, text="Set", command=self.set_gain).grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(self.param_frame, text="Trigger Mode:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.trigger_var = tk.StringVar(value="Continuous")
        self.trigger_combobox = ttk.Combobox(self.param_frame, textvariable=self.trigger_var, 
                                              values=["Continuous", "External Trigger"], width=14, state="readonly")
        self.trigger_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.trigger_combobox.bind("<<ComboboxSelected>>", self.on_trigger_mode_changed)
        ttk.Button(self.param_frame, text="Set", command=self.set_trigger).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(self.param_frame, text="Trigger Source:").grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.trigger_source_var = tk.StringVar(value="Soft Trigger")
        self.trigger_source_combobox = ttk.Combobox(self.param_frame, textvariable=self.trigger_source_var,
                                                     values=["Soft Trigger", "Line0", "Line1", "Line2", "Line3"], 
                                                     width=12, state="readonly")
        self.trigger_source_combobox.grid(row=1, column=4, padx=5, pady=5)
        ttk.Button(self.param_frame, text="Set", command=self.set_trigger_source).grid(row=1, column=5, padx=5, pady=5)

        self.soft_trigger_btn = ttk.Button(self.param_frame, text="Soft Trigger", command=self.execute_soft_trigger)
        self.soft_trigger_btn.grid(row=1, column=6, padx=5, pady=5)

        self.hide_trigger_source_controls()

        self.yolo_frame = ttk.LabelFrame(self.param_frame, text="YOLO Detection", padding="10")
        self.yolo_frame.grid(row=2, column=0, columnspan=7, pady=10, sticky=tk.W+tk.E)

        self.yolo_var = tk.BooleanVar(value=False)
        self.yolo_check = ttk.Checkbutton(self.yolo_frame, text="Enable YOLO Detection",
                                          variable=self.yolo_var, command=self.toggle_yolo)
        self.yolo_check.grid(row=0, column=0, padx=5, pady=5)

        ttk.Label(self.yolo_frame, text="Model:").grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.yolo_model_var = tk.StringVar(value="yolov8n.pt")
        self.yolo_model_combo = ttk.Combobox(self.yolo_frame, textvariable=self.yolo_model_var,
                                             values=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"],
                                             width=15, state="readonly")
        self.yolo_model_combo.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.yolo_frame, text="Conf:").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.yolo_conf_var = tk.DoubleVar(value=0.5)
        self.yolo_conf_scale = ttk.Scale(self.yolo_frame, from_=0.1, to=1.0, variable=self.yolo_conf_var,
                                        orient=tk.HORIZONTAL, length=100, command=self.update_yolo_conf)
        self.yolo_conf_scale.grid(row=0, column=4, padx=5, pady=5)
        self.yolo_conf_label = ttk.Label(self.yolo_frame, text="0.5")
        self.yolo_conf_label.grid(row=0, column=5, padx=2, pady=5)

        self.current_image = None
        self.tk_img = None
        self.current_loaded_image = None
        self.current_image_path = None
        self.detection_image = None
        self.detection_tk_img = None

        self.root.after(100, self.enum_cameras)

    def init_logs_tab(self):
        self.logs_frame = ttk.Frame(self.logs_tab, padding="10")
        self.logs_frame.pack(fill=tk.BOTH, expand=True)

        self.logs_label = ttk.Label(self.logs_frame, text="Application Logs", font=('Helvetica', 12, 'bold'))
        self.logs_label.pack(fill=tk.X, pady=5)

        self.logs_tree = ttk.Treeview(self.logs_frame, columns=('timestamp', 'level', 'source', 'message'), show='headings')
        self.logs_tree.heading('timestamp', text='Time')
        self.logs_tree.heading('level', text='Level')
        self.logs_tree.heading('source', text='Source')
        self.logs_tree.heading('message', text='Message')
        
        self.logs_tree.column('timestamp', width=150)
        self.logs_tree.column('level', width=80)
        self.logs_tree.column('source', width=100)
        self.logs_tree.column('message', width=400)
        
        self.logs_tree.pack(fill=tk.BOTH, expand=True)

        self.logs_scrollbar = ttk.Scrollbar(self.logs_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        self.logs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.logs_tree.configure(yscrollcommand=self.logs_scrollbar.set)

        self.logs_button_frame = ttk.Frame(self.logs_frame)
        self.logs_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.logs_button_frame, text="Refresh Logs", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.logs_button_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)

        self.scan_history_frame = ttk.LabelFrame(self.logs_tab, text="Scan History", padding="10")
        self.scan_history_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.scan_tree = ttk.Treeview(self.scan_history_frame, columns=('id', 'filename', 'people_count', 'scan_date', 'status'), show='headings')
        self.scan_tree.heading('id', text='ID')
        self.scan_tree.heading('filename', text='Filename')
        self.scan_tree.heading('people_count', text='Persons')
        self.scan_tree.heading('scan_date', text='Date')
        self.scan_tree.heading('status', text='Status')
        
        self.scan_tree.column('id', width=50)
        self.scan_tree.column('filename', width=200)
        self.scan_tree.column('people_count', width=80)
        self.scan_tree.column('scan_date', width=150)
        self.scan_tree.column('status', width=80)
        
        self.scan_tree.pack(fill=tk.BOTH, expand=True)

        self.scan_scrollbar = ttk.Scrollbar(self.scan_history_frame, orient=tk.VERTICAL, command=self.scan_tree.yview)
        self.scan_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scan_tree.configure(yscrollcommand=self.scan_scrollbar.set)

        self.scan_button_frame = ttk.Frame(self.scan_history_frame)
        self.scan_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.scan_button_frame, text="Refresh History", command=self.refresh_scan_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.scan_button_frame, text="Delete Selected", command=self.delete_selected_scan).pack(side=tk.LEFT, padx=5)

        self.refresh_logs()
        self.refresh_scan_history()

    def init_stats_tab(self):
        self.stats_frame = ttk.Frame(self.stats_tab, padding="20")
        self.stats_frame.pack(fill=tk.BOTH, expand=True)

        self.stats_label = ttk.Label(self.stats_frame, text="System Statistics", font=('Helvetica', 14, 'bold'))
        self.stats_label.pack(fill=tk.X, pady=10)

        self.stats_cards = ttk.Frame(self.stats_frame)
        self.stats_cards.pack(fill=tk.X, pady=10)

        self.total_scans_card = ttk.LabelFrame(self.stats_cards, text="Total Scans", padding="20")
        self.total_scans_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.total_scans_value = ttk.Label(self.total_scans_card, text="0", font=('Helvetica', 24, 'bold'))
        self.total_scans_value.pack()

        self.total_people_card = ttk.LabelFrame(self.stats_cards, text="Total Persons Detected", padding="20")
        self.total_people_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.total_people_value = ttk.Label(self.total_people_card, text="0", font=('Helvetica', 24, 'bold'))
        self.total_people_value.pack()

        self.avg_people_card = ttk.LabelFrame(self.stats_cards, text="Avg Persons/Scan", padding="20")
        self.avg_people_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.avg_people_value = ttk.Label(self.avg_people_card, text="0.0", font=('Helvetica', 24, 'bold'))
        self.avg_people_value.pack()

        self.today_scans_card = ttk.LabelFrame(self.stats_cards, text="Today's Scans", padding="20")
        self.today_scans_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.today_scans_value = ttk.Label(self.today_scans_card, text="0", font=('Helvetica', 24, 'bold'))
        self.today_scans_value.pack()

        self.success_rate_card = ttk.LabelFrame(self.stats_cards, text="Success Rate", padding="20")
        self.success_rate_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.success_rate_value = ttk.Label(self.success_rate_card, text="100%", font=('Helvetica', 24, 'bold'))
        self.success_rate_value.pack()

        self.update_stats()

        ttk.Button(self.stats_frame, text="Refresh Statistics", command=self.update_stats).pack(pady=10)

    def update_stats(self):
        stats = self.db.get_scan_stats()
        self.total_scans_value.config(text=str(stats.get('total_scans', 0)))
        self.total_people_value.config(text=str(stats.get('total_people', 0)))
        self.avg_people_value.config(text=str(stats.get('avg_people_per_scan', 0.0)))
        self.today_scans_value.config(text=str(stats.get('today_scans', 0)))
        self.success_rate_value.config(text=f"{stats.get('success_rate', 100.0)}%")

    def refresh_logs(self):
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)
        
        logs = self.db.get_all_logs(limit=200)
        for log in logs:
            timestamp = log.get('timestamp', '')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            self.logs_tree.insert('', 0, values=(
                timestamp,
                log.get('level', 'INFO'),
                log.get('source', 'app'),
                log.get('message', '')
            ))

    def refresh_scan_history(self):
        for item in self.scan_tree.get_children():
            self.scan_tree.delete(item)
        
        scans = self.db.get_all_scans()
        for scan in scans:
            scan_date = scan.get('scan_date', '')
            if isinstance(scan_date, datetime):
                scan_date = scan_date.strftime('%Y-%m-%d %H:%M:%S')
            self.scan_tree.insert('', 0, values=(
                scan.get('id', ''),
                scan.get('filename', ''),
                scan.get('people_count', 0),
                scan_date,
                scan.get('status', '')
            ))

    def clear_logs(self):
        if messagebox.askyesno("Clear Logs", "Are you sure you want to clear all logs?"):
            try:
                cursor = self.db.conn.cursor()
                cursor.execute('DELETE FROM logs')
                self.db.conn.commit()
                self.refresh_logs()
                self.db.add_log("Logs cleared by user", level="WARNING", source="app")
                messagebox.showinfo("Success", "Logs cleared successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear logs: {e}")

    def delete_selected_scan(self):
        selected = self.scan_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a scan to delete")
            return
        
        scan_id = int(self.scan_tree.item(selected[0])['values'][0])
        
        if messagebox.askyesno("Delete Scan", f"Are you sure you want to delete scan ID {scan_id}?"):
            self.db.delete_scan(scan_id)
            self.refresh_scan_history()
            self.update_stats()
            self.db.add_log(f"Scan {scan_id} deleted", level="WARNING", source="app")
            messagebox.showinfo("Success", "Scan deleted successfully")

    def on_canvas_resize(self, event):
        if self.current_image is not None:
            self.display_image(self.current_image)

    def on_detection_canvas_resize(self, event):
        if self.detection_image is not None:
            self.display_detection_image(self.detection_image)

    def enum_cameras(self):
        cameras = self.hik_camera.enum_cameras()
        if not cameras:
            cameras = ["No Camera"]
        self.camera_combobox['values'] = cameras
        if cameras:
            self.camera_var.set(cameras[0])
        self.status_var.set("Cameras Enumerated")
        self.db.add_log("Cameras enumerated", level="INFO", source="camera")

    def toggle_connection(self):
        if not self.camera_connected:
            camera_name = self.camera_var.get()
            if camera_name and camera_name != "No Camera":
                self.db.add_log(f"Connecting to camera: {camera_name}", level="INFO", source="camera")
                success = self.hik_camera.connect(camera_name)
                if success:
                    self.camera_connected = True
                    self.connect_button.config(text="Disconnect")
                    self.status_var.set(f"Connected: {camera_name}")
                    self.status_label.config(foreground="green")
                    self.stop_display = False
                    
                    # Check if we're in trigger mode
                    mode = self.trigger_var.get()
                    self.trigger_mode = (mode == "External Trigger")
                    
                    if self.trigger_mode:
                        self.display_trigger_waiting_message()
                    else:
                        self.show_image()
                        
                    self.update_camera_params()
                    self.db.add_log(f"Connected to camera: {camera_name}", level="INFO", source="camera")
                else:
                    self.status_var.set("Connection Failed")
                    self.db.add_log(f"Failed to connect to camera: {camera_name}", level="ERROR", source="camera")
        else:
            self.stop_display = True
            self.hik_camera.disconnect()
            self.camera_connected = False
            self.trigger_mode = False
            self.connect_button.config(text="Connect")
            self.status_var.set("Not Connected")
            self.status_label.config(foreground="red")
            self.current_image = None
            self.canvas.delete("all")
            self.detection_canvas.delete("all")
            self.db.add_log("Camera disconnected", level="INFO", source="camera")

    def update_camera_params(self):
        exposure = self.hik_camera.get_exposure()
        if exposure is not None:
            self.exposure_var.set(round(exposure, 2))
        
        gain = self.hik_camera.get_gain()
        if gain is not None:
            self.gain_var.set(round(gain, 2))

    def display_image(self, img):
        if img is None:
            print("[UI] display_image: img is None")
            return
        
        self.current_image = img
        
        self.root.update_idletasks()
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600
        
        if len(img.shape) == 2:
            print("[UI] Grayscale image detected, converting to BGR")
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            print("[UI] RGBA image detected, converting to BGR")
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        
        img_height, img_width = img.shape[:2]
        
        if img_height == 0 or img_width == 0:
            print(f"[UI] Invalid image dimensions: {img_width}x{img_height}")
            return
        
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height
        scale = min(scale_w, scale_h)
        
        if scale < 1:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        else:
            new_width = img_width
            new_height = img_height
            img_resized = img
        
        if img_resized.size == 0:
            print("[UI] Resized image is empty")
            return
        
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        if pil_img.width == 0 or pil_img.height == 0:
            print(f"[UI] PIL image has invalid dimensions: {pil_img.width}x{pil_img.height}")
            return
        
        self.tk_img = ImageTk.PhotoImage(pil_img)
        
        self.canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.tk_img)
        
        print(f"[UI] Image displayed: {img_width}x{img_height} -> {new_width}x{new_height}")

    def display_detection_image(self, img):
        if img is None:
            print("display_detection_image: img is None")
            return
        
        self.detection_image = img
        
        self.root.update_idletasks()
        
        canvas_width = self.detection_canvas.winfo_width()
        canvas_height = self.detection_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600
        
        img_height, img_width = img.shape[:2]
        
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height
        scale = min(scale_w, scale_h)
        
        if scale < 1:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        else:
            new_width = img_width
            new_height = img_height
            img_resized = img
        
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        self.detection_tk_img = ImageTk.PhotoImage(pil_img)
        
        self.detection_canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        self.detection_canvas.create_image(x, y, anchor=tk.NW, image=self.detection_tk_img)

    def show_image(self):
        if self.camera_connected and not self.stop_display:
            if self.trigger_mode:
                # In trigger mode, don't continuously refresh - wait for trigger
                self.root.after(100, self.show_image)
                return
                
            # Normal continuous mode
            img = self.hik_camera.get_image()

            if img is None:
                print("[UI] Camera returned None image")
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(img, f"Connected: {self.camera_var.get()}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(img, "Waiting for frames...", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                if len(img.shape) == 2:
                    print(f"[UI] Received grayscale image: {img.shape}")
                else:
                    print(f"[UI] Received color image: {img.shape}")

            if self.yolo_detector.enabled:
                img, detections = self.yolo_detector.detect(img)
                if detections:
                    det_text = f"Detections: {len(detections)}"
                    cv2.putText(img, det_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            self.display_image(img)
            self.root.after(30, self.show_image)

    def set_exposure(self):
        exposure = self.exposure_var.get()
        success = self.hik_camera.set_exposure(exposure)
        if success:
            self.status_var.set(f"Exposure Set: {exposure}ms")
            self.db.add_log(f"Exposure set to {exposure}ms", level="INFO", source="camera")
        else:
            self.status_var.set("Set Exposure Failed")
            self.db.add_log(f"Failed to set exposure to {exposure}ms", level="ERROR", source="camera")

    def set_gain(self):
        gain = self.gain_var.get()
        success = self.hik_camera.set_gain(gain)
        if success:
            self.status_var.set(f"Gain Set: {gain}dB")
            self.db.add_log(f"Gain set to {gain}dB", level="INFO", source="camera")
        else:
            self.status_var.set("Set Gain Failed")
            self.db.add_log(f"Failed to set gain to {gain}dB", level="ERROR", source="camera")

    def on_trigger_mode_changed(self, event=None):
        mode = self.trigger_var.get()
        if mode == "External Trigger":
            self.show_trigger_source_controls()
        else:
            self.hide_trigger_source_controls()

    def show_trigger_source_controls(self):
        self.trigger_source_combobox.grid()
        self.soft_trigger_btn.grid()

    def hide_trigger_source_controls(self):
        self.trigger_source_combobox.grid_remove()
        self.soft_trigger_btn.grid_remove()

    def set_trigger(self):
        mode = self.trigger_var.get()
        success = self.hik_camera.set_trigger_mode(mode)
        if success:
            self.trigger_mode = (mode == "External Trigger")
            self.status_var.set(f"Trigger Mode Set: {mode}")
            self.db.add_log(f"Trigger mode set to {mode}", level="INFO", source="camera")
            if mode == "External Trigger":
                self.show_trigger_source_controls()
                # Show waiting message in trigger mode
                if self.camera_connected:
                    self.display_trigger_waiting_message()
            else:
                self.hide_trigger_source_controls()
        else:
            self.status_var.set("Set Trigger Mode Failed")
            self.db.add_log(f"Failed to set trigger mode to {mode}", level="ERROR", source="camera")

    def set_trigger_source(self):
        source = self.trigger_source_var.get()
        success = self.hik_camera.set_trigger_source(source)
        if success:
            self.status_var.set(f"Trigger Source Set: {source}")
            self.db.add_log(f"Trigger source set to {source}", level="INFO", source="camera")
        else:
            self.status_var.set("Set Trigger Source Failed")
            self.db.add_log(f"Failed to set trigger source to {source}", level="ERROR", source="camera")

    def execute_soft_trigger(self):
        self.status_var.set("Executing soft trigger...")
        self.db.add_log("Executing soft trigger...", level="INFO", source="camera")
        
        # Execute the software trigger command
        success = self.hik_camera.soft_trigger()
        
        if success:
            self.status_var.set("Soft Trigger Executed - Capturing Image...")
            
            # Try to get the triggered image - wait a bit and try multiple times
            captured_img = None
            for attempt in range(5):  # Try up to 5 times
                captured_img = self.hik_camera.get_image()
                if captured_img is not None and len(captured_img.shape) >= 2:
                    print(f"[Trigger] Image captured successfully on attempt {attempt+1}")
                    break
                import time
                time.sleep(0.1)  # Small delay between attempts
            
            if captured_img is not None:
                # Display the original image on the left
                self.display_image(captured_img.copy())
                self.current_trigger_image = captured_img.copy()
                
                # Run YOLO detection and show result on the right
                self.process_triggered_image(captured_img)
                
                self.status_var.set("Soft Trigger Complete - Detection Finished")
            else:
                self.status_var.set("Soft Trigger Failed - Could not capture image")
                self.db.add_log("Soft trigger failed - could not capture image", level="ERROR", source="camera")
        else:
            self.status_var.set("Soft Trigger Failed")
            self.db.add_log("Soft trigger failed", level="ERROR", source="camera")

    def display_trigger_waiting_message(self):
        # Show a waiting message in trigger mode
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "Camera in Trigger Mode", (120, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img, "Click 'Soft Trigger' or wait for external trigger", (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        self.display_image(img)
        self.detection_canvas.delete("all")
        
    def process_triggered_image(self, img):
        # Run YOLO detection on the triggered image and save to database
        from datetime import datetime
        
        self.status_var.set("Running YOLO detection...")
        
        # Make sure YOLO model is loaded
        if self.yolo_detector.model is None:
            if not self.yolo_detector.load_model():
                self.status_var.set("YOLO model not available")
                return
        
        try:
            detection_img = img.copy()
            
            # Run YOLO detection
            results = self.yolo_detector.model(
                detection_img,
                conf=self.yolo_detector.conf_threshold,
                iou=self.yolo_detector.iou_threshold,
                verbose=False
            )
            
            person_count = 0
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confs = result.boxes.conf.cpu().numpy()
                    classes = result.boxes.cls.cpu().numpy().astype(int)
                    
                    for box, conf, cls in zip(boxes, confs, classes):
                        if cls == 0:  # Class 0 is person
                            person_count += 1
                            x1, y1, x2, y2 = map(int, box)
                            detections.append((x1, y1, x2, y2, conf))
                            
                            # Draw red bounding box
                            cv2.rectangle(detection_img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            
                            label = f"Person: {conf:.2f}"
                            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                            cv2.rectangle(detection_img, (x1, y1 - label_size[1] - 10), 
                                        (x1 + label_size[0], y1), (0, 0, 255), -1)
                            cv2.putText(detection_img, label, (x1, y1 - 5), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Add detection count text
            det_text = f"Persons Detected: {person_count}"
            cv2.putText(detection_img, det_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display detection result on the right
            self.display_detection_image(detection_img)
            
            # Save to database
            start_time = datetime.now()
            timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"trigger_{timestamp}.jpg"
            
            scan_id = self.db.add_scan(
                image_path="",  # Optional - we could save to disk too
                filename=filename,
                people_count=person_count,
                detection_time=0.0,
                confidence_threshold=self.yolo_detector.conf_threshold,
                model_used="yolov8n.pt",
                status="success"
            )
            
            # Save detection details
            for det in detections:
                x1, y1, x2, y2, conf = det
                self.db.add_scan_detail(scan_id, (x1, y1, x2, y2), conf, "person")
            
            self.db.add_log(f"Trigger detection completed: {person_count} persons found", 
                          level="INFO", source="camera", scan_id=scan_id)
            
            # Update logs and statistics
            self.refresh_logs()
            self.refresh_scan_history()
            self.update_stats()
            
        except Exception as e:
            print(f"[ERROR] Trigger image processing failed: {e}")
            import traceback
            traceback.print_exc()
            self.status_var.set("Detection processing failed")
            self.db.add_log(f"Trigger processing error: {e}", level="ERROR", source="camera")

    def toggle_yolo(self):
        enabled = self.yolo_var.get()
        if enabled:
            model_name = self.yolo_model_var.get()
            if self.yolo_detector.model is None or self.yolo_detector.model_name != model_name:
                self.yolo_detector.model_name = model_name
                self.db.add_log(f"Loading YOLO model: {model_name}", level="INFO", source="yolo")
                if not self.yolo_detector.load_model():
                    self.yolo_var.set(False)
                    self.status_var.set("YOLO Model Load Failed")
                    self.db.add_log(f"YOLO model load failed: {model_name}", level="ERROR", source="yolo")
                    return
                self.db.add_log(f"YOLO model loaded successfully: {model_name}", level="INFO", source="yolo")
            self.yolo_detector.enabled = True
            self.status_var.set(f"YOLO Detection Enabled ({model_name})")
            self.db.add_log("YOLO detection enabled", level="INFO", source="yolo")
        else:
            self.yolo_detector.enabled = False
            self.status_var.set("YOLO Detection Disabled")
            self.db.add_log("YOLO detection disabled", level="INFO", source="yolo")

    def update_yolo_conf(self, value):
        conf = float(value)
        self.yolo_detector.set_confidence(conf)
        self.yolo_conf_label.config(text=f"{conf:.1f}")

    def load_local_image(self):
        self.stop_display = True
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*")
            ]
        )

        print(f"Selected file: {file_path}")

        if file_path:
            try:
                img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    print(f"Image loaded: {img.shape}")
                    
                    self.current_loaded_image = img.copy()
                    self.current_image_path = file_path
                    
                    self.display_image(self.current_loaded_image.copy())

                    self.detect_persons()

                    self.status_var.set(f"Loaded: {file_path}")
                    self.db.add_log(f"Image loaded: {file_path}", level="INFO", source="app")
                else:
                    print(f"Failed to load image: {file_path}")
                    self.status_var.set("Failed to load image")
                    self.db.add_log(f"Failed to load image: {file_path}", level="ERROR", source="app")
            except Exception as e:
                print(f"Error loading image: {e}")
                import traceback
                traceback.print_exc()
                self.status_var.set(f"Error loading image: {e}")
                self.db.add_log(f"Error loading image: {e}", level="ERROR", source="app")
    
    def detect_persons(self):
        if self.current_loaded_image is None:
            self.status_var.set("No image loaded")
            return
        
        start_time = datetime.now()
        
        try:
            self.status_var.set("Detecting persons...")
            
            detection_img = self.current_loaded_image.copy()
            
            if self.yolo_detector.model is None:
                print("Loading YOLO model...")
                self.status_var.set("Downloading YOLO model...")
                self.root.update()
                model_name = "yolov8n.pt"
                self.db.add_log(f"Downloading YOLO model: {model_name}", level="INFO", source="yolo")
                if not self.yolo_detector.load_model(model_name):
                    self.status_var.set("YOLO model load failed")
                    self.db.add_log("YOLO model download failed", level="ERROR", source="yolo")
                    return
                self.db.add_log("YOLO model downloaded and loaded successfully", level="INFO", source="yolo")
            
            results = self.yolo_detector.model(
                detection_img,
                conf=self.yolo_detector.conf_threshold,
                iou=self.yolo_detector.iou_threshold,
                verbose=False
            )
            
            person_count = 0
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confs = result.boxes.conf.cpu().numpy()
                    classes = result.boxes.cls.cpu().numpy().astype(int)
                    
                    for box, conf, cls in zip(boxes, confs, classes):
                        if cls == 0:
                            person_count += 1
                            x1, y1, x2, y2 = map(int, box)
                            detections.append((x1, y1, x2, y2, conf))
                            
                            cv2.rectangle(detection_img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            
                            label = f"Person: {conf:.2f}"
                            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                            cv2.rectangle(detection_img, (x1, y1 - label_size[1] - 10), 
                                        (x1 + label_size[0], y1), (0, 0, 255), -1)
                            cv2.putText(detection_img, label, (x1, y1 - 5), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
            det_text = f"Persons Detected: {person_count}"
            cv2.putText(detection_img, det_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            self.display_detection_image(detection_img)
            
            end_time = datetime.now()
            detection_time = (end_time - start_time).total_seconds()
            
            filename = self.current_image_path.split('/')[-1] if self.current_image_path else "unknown"
            
            scan_id = self.db.add_scan(
                image_path=self.current_image_path or "",
                filename=filename,
                people_count=person_count,
                detection_time=detection_time,
                confidence_threshold=self.yolo_detector.conf_threshold,
                model_used="yolov8n.pt",
                status="success"
            )
            
            for det in detections:
                x1, y1, x2, y2, conf = det
                self.db.add_scan_detail(scan_id, (x1, y1, x2, y2), conf, "person")
            
            self.db.add_log(f"Person detection completed: {person_count} persons in {detection_time:.2f}s", 
                          level="INFO", source="yolo", scan_id=scan_id)
            
            self.status_var.set(f"Person detection complete: {person_count} persons found")
            
            self.refresh_logs()
            self.refresh_scan_history()
            self.update_stats()
            
        except Exception as e:
            print(f"Person detection error: {e}")
            import traceback
            traceback.print_exc()
            self.status_var.set("Person detection error")
            self.db.add_log(f"Person detection error: {e}", level="ERROR", source="yolo")
            self.detection_canvas.delete("all")

if __name__ == "__main__":
    root = tk.Tk()
    app = HikCameraApp(root)
    root.mainloop()
