import os
import shutil
import requests
from PIL import Image
from PIL.ExifTags import TAGS
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

# Cache for reverse geocoding results to avoid duplicate lookups
geocode_cache = {}

def reverse_geocode(lat, lon):
    """
    Use OpenStreetMap Nominatim to reverse geocode latitude and longitude to a place name.
    Results are cached for speed and to avoid rate limits.
    """
    try:
        key = (round(lat, 5), round(lon, 5))  # rounding to reduce cache size
        if key in geocode_cache:
            return geocode_cache[key]

        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 16,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "MetadataViewer/1.0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            # Try to get the most human-friendly location
            for key_name in ["suburb", "city", "town", "village", "hamlet"]:
                if key_name in address:
                    geocode_cache[key] = address[key_name]
                    return address[key_name]
            geocode_cache[key] = "Unknown"
            return "Unknown"
        elif response.status_code == 429:
            geocode_cache[key] = "Rate limited"
            return "Rate limited"
        elif response.status_code == 403:
            geocode_cache[key] = "Forbidden (possible ban)"
            return "Forbidden (possible ban)"
        else:
            geocode_cache[key] = "Reverse geocoding failed"
            return "Reverse geocoding failed"
    except Exception as e:
        geocode_cache[key] = f"Reverse geocoding error: {e}"
        return f"Reverse geocoding error: {e}"

def sanitize_filename(s):
    """
    Replace characters that are invalid in Windows filenames with underscores.
    """
    invalid = '<>:"/\\|?*'
    for c in invalid:
        s = s.replace(c, '_')
    return s.strip()

def move_video_to_folder(video_path, failed_folder, log_callback=None, dest_folder=None):
    """
    Move video files to a 'videos' subfolder in the destination folder, keeping the original filename.
    If a file with the same name exists, append a counter.
    """
    try:
        videos_folder = os.path.join(dest_folder, "videos")
        if not os.path.exists(videos_folder):
            os.makedirs(videos_folder)

        new_path = os.path.join(videos_folder, os.path.basename(video_path))

        # Avoid overwriting files
        counter = 1
        base, ext = os.path.splitext(os.path.basename(video_path))
        while os.path.exists(new_path):
            new_path = os.path.join(videos_folder, f"{base}_{counter}{ext}")
            counter += 1

        shutil.move(video_path, new_path)
        msg = f"Moved video to: {os.path.relpath(new_path, dest_folder) if dest_folder else new_path}"
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
    except Exception as e:
        # If moving fails, move to a failed folder sorted by file type
        msg = f"Error moving video {video_path}: {e}"
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
        try:
            ext = os.path.splitext(video_path)[1].lower().replace('.', '')
            failed_type_folder = os.path.join(failed_folder, ext if ext else "other")
            if not os.path.exists(failed_type_folder):
                os.makedirs(failed_type_folder)
            shutil.move(video_path, os.path.join(failed_type_folder, os.path.basename(video_path)))
            msg = f"Moved {video_path} to {failed_type_folder}"
            if log_callback:
                log_callback(msg)
            else:
                print(msg)
        except Exception as move_e:
            msg = f"Failed to move {video_path} to {failed_type_folder}: {move_e}"
            if log_callback:
                log_callback(msg)
            else:
                print(msg)

def get_exif_data(image_path, failed_folder, log_callback=None, dest_folder=None):
    """
    Extract device, location, date, and time EXIF data from an image and rename the file.
    Move the file into a subfolder of dest_folder based on date (YYYYMMDD).
    """
    try:
        with Image.open(image_path) as image:
            exif_data = image._getexif() if hasattr(image, '_getexif') else None

            make = model = datetime = location = "Unknown"

            if exif_data:
                # Convert EXIF tag numbers to names
                exif = {TAGS.get(tag, tag): value for tag, value in exif_data.items()}
                make = exif.get('Make', 'Unknown')
                model = exif.get('Model', 'Unknown')
                datetime = exif.get('DateTimeOriginal', exif.get('DateTime', 'Unknown'))
                if datetime and datetime != "Unknown":
                    # Format date as YYYYMMDD
                    datetime = datetime.replace(":", "").replace(" ", "_")[:8]
                else:
                    datetime = "Unknown"

                gps_info = exif.get('GPSInfo')
                if gps_info:
                    # Helper functions for GPS conversion
                    def to_float(x):
                        try:
                            return float(x[0]) / float(x[1])
                        except TypeError:
                            return float(x)
                    def _convert_to_degrees(value):
                        d, m, s = value
                        return to_float(d) + (to_float(m) / 60.0) + (to_float(s) / 3600.0)

                    gps_latitude = gps_info.get(2)
                    gps_latitude_ref = gps_info.get(1)
                    gps_longitude = gps_info.get(4)
                    gps_longitude_ref = gps_info.get(3)
                    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                        lat = _convert_to_degrees(gps_latitude)
                        if gps_latitude_ref != 'N':
                            lat = -lat
                        lon = _convert_to_degrees(gps_longitude)
                        if gps_longitude_ref != 'E':
                            lon = -lon
                        location = reverse_geocode(lat, lon)
                    else:
                        location = "Unknown"
                else:
                    location = "Unknown"
            else:
                # For PNG and other formats with limited metadata
                info = image.info
                if info:
                    datetime = info.get('date:create', info.get('date:modify', 'Unknown'))
                    if datetime and datetime != "Unknown":
                        datetime = datetime.replace(":", "").replace(" ", "_")[:8]
                    make = info.get('Software', 'Unknown')
                    model = info.get('Description', 'Unknown')
                location = "Unknown"

        # Clean up filename parts
        datetime = sanitize_filename(str(datetime))
        location = sanitize_filename(str(location))
        model = sanitize_filename(str(model))

        # Create date-based subfolder in destination
        if dest_folder and datetime != "Unknown":
            date_folder = os.path.join(dest_folder, datetime)
        elif dest_folder:
            date_folder = dest_folder
        else:
            date_folder = os.path.dirname(image_path)

        if not os.path.exists(date_folder):
            os.makedirs(date_folder)

        # Build new filename in date-based folder
        ext = os.path.splitext(image_path)[1]
        new_path = os.path.join(date_folder, f"{datetime}_{location}_{model}{ext}")

        # Avoid overwriting files
        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(date_folder, f"{datetime}_{location}_{model}_{counter}{ext}")
            counter += 1

        shutil.move(image_path, new_path)
        msg = f"Renamed and moved to: {os.path.relpath(new_path, dest_folder) if dest_folder else new_path}"
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    except Exception as e:
        # If anything fails, move to a failed folder sorted by file type
        msg = f"Error processing {image_path}: {e}"
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
        try:
            ext = os.path.splitext(image_path)[1].lower().replace('.', '')
            failed_type_folder = os.path.join(failed_folder, ext if ext else "other")
            if not os.path.exists(failed_type_folder):
                os.makedirs(failed_type_folder)
            shutil.move(image_path, os.path.join(failed_type_folder, os.path.basename(image_path)))
            msg = f"Moved {image_path} to {failed_type_folder}"
            if log_callback:
                log_callback(msg)
            else:
                print(msg)
        except Exception as move_e:
            msg = f"Failed to move {image_path} to {failed_type_folder}: {move_e}"
            if log_callback:
                log_callback(msg)
            else:
                print(msg)

def run_gui():
    """
    Launch the main GUI for the metadata organiser.
    """
    def select_folder():
        # Let the user pick the source folder
        folder = filedialog.askdirectory(title="Select Source Folder with Images")
        if folder:
            folder_var.set(folder)

    def select_dest_folder():
        # Let the user pick the destination folder
        folder = filedialog.askdirectory(title="Select Destination Folder for Renamed Images")
        if folder:
            dest_folder_var.set(folder)

    def start_processing():
        # Run the processing in a background thread to keep the GUI responsive
        def process_files():
            src_folder = folder_var.get()
            dest_folder = dest_folder_var.get()
            if not src_folder or not os.path.isdir(src_folder):
                messagebox.showerror("Error", "Please select a valid source folder.")
                return
            if not dest_folder or not os.path.isdir(dest_folder):
                messagebox.showerror("Error", "Please select a valid destination folder.")
                return
            log_text.delete(1.0, tk.END)
            supported_exts = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
            video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV', '.AVI', '.MKV')

            # Recursively collect all files in src_folder and subfolders
            files = []
            for root_dir, _, filenames in os.walk(src_folder):
                for f in filenames:
                    files.append(os.path.join(root_dir, f))
            total_files = len(files)
            progress_bar["maximum"] = total_files
            progress_bar["value"] = 0

            def log_and_update(msg):
                # Log progress and update the progress bar
                log_text.insert(tk.END, msg + "\n")
                log_text.see(tk.END)
                progress_bar["value"] += 1
                root.update_idletasks()

            failed_folder = os.path.join(dest_folder, "failed_renames")

            for src_path in files:
                filename = os.path.basename(src_path)
                if filename.lower().endswith(supported_exts):
                    try:
                        get_exif_data(src_path, failed_folder, log_and_update, dest_folder=dest_folder)
                    except Exception as e:
                        log_and_update(f"Error processing {src_path}: {e}")
                elif filename.lower().endswith(video_exts):
                    try:
                        move_video_to_folder(src_path, failed_folder, log_and_update, dest_folder=dest_folder)
                    except Exception as e:
                        log_and_update(f"Error moving video {src_path}: {e}")
                else:
                    # Move unsupported files to a failed folder sorted by file type
                    try:
                        ext = os.path.splitext(src_path)[1].lower().replace('.', '')
                        failed_type_folder = os.path.join(failed_folder, ext if ext else "other")
                        if not os.path.exists(failed_type_folder):
                            os.makedirs(failed_type_folder)
                        shutil.move(src_path, os.path.join(failed_type_folder, filename))
                        log_and_update(f"Moved unsupported file {src_path} to {failed_type_folder}")
                    except Exception as move_e:
                        log_and_update(f"Failed to move unsupported file {src_path} to {failed_type_folder}: {move_e}")

            messagebox.showinfo("Done", "Processing complete.")

        # Start the file processing in a background thread
        threading.Thread(target=process_files, daemon=True).start()

    # --- GUI Layout ---
    root = tk.Tk()
    root.title("Metadata Organiser")

    frame = tk.Frame(root, padx=10, pady=10)
    frame.pack(fill=tk.BOTH, expand=True)

    folder_var = tk.StringVar()
    dest_folder_var = tk.StringVar()

    tk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky="w")
    tk.Entry(frame, textvariable=folder_var, width=50).grid(row=0, column=1, padx=5)
    tk.Button(frame, text="Browse...", command=select_folder).grid(row=0, column=2)

    tk.Label(frame, text="Destination Folder:").grid(row=1, column=0, sticky="w")
    tk.Entry(frame, textvariable=dest_folder_var, width=50).grid(row=1, column=1, padx=5)
    tk.Button(frame, text="Browse...", command=select_dest_folder).grid(row=1, column=2)

    tk.Button(frame, text="Start", command=start_processing).grid(row=2, column=0, columnspan=3, pady=10)

    from tkinter import ttk
    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=400, mode="determinate")
    progress_bar.grid(row=3, column=0, columnspan=3, pady=5)

    log_text = tk.Text(frame, width=80, height=20)
    log_text.grid(row=4, column=0, columnspan=3)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
