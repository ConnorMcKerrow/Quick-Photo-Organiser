# Quick Photo Organiser

**Quick Photo Organiser** is a lightweight Python application that I developed for sorting, renaming, and organizing photo and video files using metadata such as date, camera model, and GPS location. I developed this program becuase after a long photoshoot I always hate sorting my photos and wanted a tool to do it for me. It includes a graphical interface, supports recursive folder processing, and features automatic date-based organization with error handling.

> Note: This project was built with a practical focus and is approximately 90% “vibe-coded.” It works well for my personal use but is not intended as production-grade software.

---

## Features

- **Graphical Interface** – Easily select source and destination folders.
- **Metadata-Based Renaming** – Images are renamed using date, reverse-geocoded location, and camera model.
- **Date-Based Organization** – Files are moved into subfolders named by date (`YYYYMMDD`).
- **Video Support** – Video files are moved (not renamed) to a dedicated `videos` subfolder.
- **Error Handling** – Files that can’t be processed are moved to a `failed_renames/` folder, grouped by file type.
- **Progress Tracking** – Real-time progress bar and logging.

---

## Requirements

- Python 3.7 or later  
- [Pillow](https://pypi.org/project/Pillow/)  
- [requests](https://pypi.org/project/requests/)  
- [tkinter](https://docs.python.org/3/library/tkinter.html) (included with most Python installations)

### Install dependencies

```bash
pip install pillow requests
```

---

## Usage

1. **Install dependencies** (see above).
2. **Run the application:**

```bash
python Metadata_viewer.py
```

3. **Using the GUI**:
   - Select the source folder (your unsorted images/videos).
   - Select the destination folder (where sorted files will be stored).
   - Click **Start** to begin.
   - Monitor progress and logs through the interface.

---

## How It Works

- **Images**:
  - Extracts EXIF metadata (date, camera, GPS).
  - Renames and organizes images into date-based folders.
  - If GPS data is available, reverse geocodes it to a location using the OpenStreetMap Nominatim API, with caching to minimise requests.

- **Videos**:
  - Moved to a `videos` subfolder in the destination directory. Filenames are unchanged.

- **Unsupported or Failed Files**:
  - Moved to `failed_renames/<filetype>/` in the destination folder for later review.

---

## Troubleshooting

- **Unresponsive UI**:  
  The application uses background threads to stay responsive. Large batches on slow drives may still cause brief freezing.

- **API Rate Limits**:  
  If you see "Rate limited" or "Forbidden" messages, it means OpenStreetMap’s API is throttling requests. The program caches results to help minimize this.

- **File Access Issues**:  
  Ensure media files aren't open in other programs during processing.

---

## Customization

- **File Type Support**:  
  Supported extensions can be modified in the script via the `supported_exts` and `video_exts` tuples.

- **Geocoding Service**:  
  By default, the app uses OpenStreetMap’s Nominatim API. You may replace this with another service if desired.

---

## License and Reuse

MIT License

Copyright (c) 2025 Connor McKerrow

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Credits

- [Pillow](https://python-pillow.org/) – image metadata handling  
- [requests](https://docs.python-requests.org/) – HTTP requests  
- [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) – reverse geocoding

---

## Example Output Structure

```
destination_folder/
├── 20240607/
│   ├── 20240607_London_Canon.jpg
│   └── 20240607_Unknown_Unknown.png
├── videos/
│   ├── myvideo.mp4
│   └── myvideo_1.mp4
└── failed_renames/
    ├── jpg/
    ├── png/
    └── mp4/
```

---

## Contact

To report issues or suggest improvements, feel free to open an issue in the repository I'd love to hear from you.
