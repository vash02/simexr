# SimExR Video Integration Guide

## 🎬 How to Add Your Demo Videos

### 📁 Step 1: Organize Your Video Files

1. **Place videos in the `docs/videos/` directory**:
   ```
   docs/
   ├── videos/
   │   ├── end-to-end-demo.mp4          # Complete workflow
   │   ├── import-demo.mp4              # Import & Transform
   │   ├── parameter-demo.mp4           # Parameter Extraction
   │   ├── execution-demo.mp4           # Safe Execution
   │   ├── reasoning-demo.mp4           # AI Analysis
   │   ├── visualization-demo.mp4       # Data Visualization
   │   └── research-demo.mp4            # Research Workflow
   ```

2. **Recommended video formats**:
   - **MP4 (H.264)** - Best compatibility across browsers
   - **WebM** - Good compression, web-optimized
   - **MOV** - High quality, larger file size

### 🔧 Step 2: Update HTML Files

#### For `demos.html`:
1. Find the video placeholder sections
2. Uncomment the `<video>` tags
3. Update the `src` attributes to point to your video files

**Example**:
```html
<!-- Replace this placeholder: -->
<div class="video-placeholder">
    <span class="upload-icon">🎥</span>
    <strong>End-to-End Workflow Demo</strong><br>
    Place your complete workflow video here:<br>
    <code>videos/end-to-end-demo.mp4</code>
</div>

<!-- With this video element: -->
<video controls poster="videos/end-to-end-poster.jpg">
    <source src="videos/end-to-end-demo.mp4" type="video/mp4">
    <source src="videos/end-to-end-demo.webm" type="video/webm">
    Your browser does not support the video tag.
</video>
```

### 📊 Step 3: Optimize for Web

#### Video Compression:
- **Resolution**: 1920x1080 or 1280x720
- **Frame Rate**: 30 FPS
- **Bitrate**: 2-5 Mbps for good quality/size balance
- **Duration**: Keep individual demos under 3 minutes

#### Tools for Compression:
- **FFmpeg** (command line):
  ```bash
  ffmpeg -i input.mov -c:v libx264 -crf 23 -c:a aac -b:a 128k output.mp4
  ```
- **HandBrake** (GUI)
- **Online tools**: CloudConvert, Online-Convert

### 🎯 Step 4: Add Video Descriptions

Update the text descriptions in `demos.html` to match your actual demo content:

```html
<div class="feature-demo">
    <span class="icon">📥</span>
    <h3>Import & Transform</h3>
    <p>Watch how SimExR imports a Lotka-Volterra model from GitHub and automatically transforms it into a standardized simulation function with parameter extraction.</p>
    <!-- Video here -->
</div>
```

### 🚀 Step 5: Test and Deploy

1. **Local Testing**:
   ```bash
   cd docs
   python -m http.server 8080
   # Visit http://localhost:8080/demos.html
   ```

2. **Check Video Playback**:
   - Videos load properly
   - Controls work (play, pause, volume)
   - Multiple format fallbacks work

3. **Deploy to GitHub Pages**:
   ```bash
   git add docs/videos/ docs/demos.html docs/documentation.html
   git commit -m "Add demo videos to documentation"
   git push origin main
   ```

### 📱 Advanced Features

#### Add Video Thumbnails:
```html
<video controls poster="videos/thumbnail.jpg">
    <source src="videos/demo.mp4" type="video/mp4">
</video>
```

#### Auto-play for GIFs:
```html
<img src="videos/quick-demo.gif" alt="Quick Demo" style="width: 100%; border-radius: 10px;">
```

#### Video with Captions:
```html
<video controls>
    <source src="videos/demo.mp4" type="video/mp4">
    <track kind="captions" src="videos/demo.vtt" srclang="en" label="English">
</video>
```

### 🎨 Styling Options

The videos are already styled with:
- Responsive width (100%)
- Rounded corners
- Box shadows
- Hover effects

You can customize the styling in the CSS sections of each HTML file.

### 📋 Checklist

- [ ] Videos placed in `docs/videos/` directory
- [ ] Video files compressed and optimized
- [ ] HTML updated with proper video tags
- [ ] Descriptions updated to match content
- [ ] Local testing completed
- [ ] Deployed to GitHub Pages
- [ ] All videos play correctly on different browsers

### 🎯 Result

Your documentation will now feature:
- **Professional video demonstrations**
- **Feature-specific showcases**
- **Interactive navigation**
- **Responsive design**
- **Cross-browser compatibility**

The videos will help users understand SimExR's capabilities visually and make the documentation much more engaging!
