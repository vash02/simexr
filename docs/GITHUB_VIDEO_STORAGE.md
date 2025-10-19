# GitHub Video Storage Guide for SimExR Documentation

## 🎬 Video Storage Options for GitHub Pages

### 📋 The Challenge
GitHub has file size limits that make storing large video files challenging:
- **Regular files**: 100MB limit per file
- **Repository size**: 1GB soft limit
- **GitHub Pages**: Serves files directly from repository

### 🎯 Recommended Solutions

## Option 1: Git LFS (Large File Storage) ⭐ RECOMMENDED

**Best for**: Video files > 25MB, professional documentation

### Setup Git LFS:
```bash
# Install Git LFS (if not already installed)
brew install git-lfs  # macOS
# or download from: https://git-lfs.github.io/

# Initialize LFS in your repository
cd /path/to/simexr_mod
git lfs install

# Track video files
git lfs track "docs/videos/*.mov"
git lfs track "docs/videos/*.mp4"
git lfs track "docs/videos/*.webm"

# Add the .gitattributes file
git add .gitattributes

# Add and commit your videos
git add docs/videos/
git commit -m "Add demo videos with Git LFS"
git push origin main
```

### Benefits:
✅ Videos stored efficiently  
✅ GitHub Pages serves them normally  
✅ No external dependencies  
✅ Version control for videos  

### Limitations:
- 1GB free LFS storage per month
- Additional storage costs $5/month per 50GB

---

## Option 2: GitHub Releases

**Best for**: Large files, occasional updates

### Steps:
1. **Create a Release**:
   - Go to your GitHub repository
   - Click "Releases" → "Create a new release"
   - Tag version: `v1.0-videos`
   - Title: "SimExR Demo Videos"

2. **Attach Videos**:
   - Drag and drop your .mov files
   - GitHub allows up to 2GB per file in releases

3. **Update HTML**:
   ```html
   <video controls preload="metadata" width="100%">
       <source src="https://github.com/vash02/simexr/releases/download/v1.0-videos/import_model.mov" type="video/quicktime">
   </video>
   ```

### Benefits:
✅ No file size limits  
✅ Free storage  
✅ Direct download links  

### Limitations:
- URLs are longer and less clean
- Videos not in main repository

---

## Option 3: External Video Hosting

**Best for**: Public documentation, SEO benefits

### YouTube (Public):
```html
<div class="video-container">
    <iframe width="100%" height="315" 
            src="https://www.youtube.com/embed/YOUR_VIDEO_ID" 
            frameborder="0" allowfullscreen>
    </iframe>
</div>
```

### Vimeo (Professional):
```html
<div class="video-container">
    <iframe src="https://player.vimeo.com/video/YOUR_VIDEO_ID" 
            width="100%" height="315" frameborder="0" allowfullscreen>
    </iframe>
</div>
```

### Benefits:
✅ No storage costs  
✅ Professional video player  
✅ Analytics and engagement metrics  
✅ Automatic transcoding and optimization  

### Limitations:
- External dependency
- May require account setup
- Less control over player appearance

---

## Option 4: Convert to Web-Optimized Formats

**Best for**: Reducing file sizes, better compatibility

### Convert MOV to MP4:
```bash
# Using FFmpeg (install: brew install ffmpeg)
ffmpeg -i input.mov -c:v libx264 -crf 23 -c:a aac -b:a 128k output.mp4

# Batch convert all videos
for file in *.mov; do
    ffmpeg -i "$file" -c:v libx264 -crf 23 -c:a aac -b:a 128k "${file%.mov}.mp4"
done
```

### Create WebM versions:
```bash
ffmpeg -i input.mov -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus output.webm
```

### Update HTML with multiple formats:
```html
<video controls preload="metadata" width="100%">
    <source src="videos/import_model.mp4" type="video/mp4">
    <source src="videos/import_model.webm" type="video/webm">
    <source src="videos/import_model.mov" type="video/quicktime">
    <p>Your browser does not support the video tag.</p>
</video>
```

---

## 🎯 Recommended Approach for SimExR

### For Your Current Setup:

1. **Convert videos to MP4** (better browser compatibility):
   ```bash
   cd docs/videos
   for file in *.mov; do
       ffmpeg -i "$file" -c:v libx264 -crf 23 -c:a aac -b:a 128k "${file%.mov}.mp4"
   done
   ```

2. **Use Git LFS** for the MP4 files:
   ```bash
   git lfs track "docs/videos/*.mp4"
   git add .gitattributes
   git add docs/videos/*.mp4
   git commit -m "Add optimized MP4 videos with Git LFS"
   ```

3. **Update HTML** to use MP4 files:
   ```html
   <source src="videos/import_model.mp4" type="video/mp4">
   ```

### File Size Targets:
- **Import demo**: ~10-15MB (from 33MB)
- **Parameter demo**: ~6-8MB (from 17MB)  
- **Run simulation**: ~8-10MB (from 18MB)
- **View results**: ~3-4MB (from 8MB)
- **AI analysis**: ~6-8MB (from 15MB)

---

## 🔧 Quick Fix for Current Issues

### Why videos aren't playing:
1. **MOV format**: Not all browsers support QuickTime MOV
2. **File size**: Large files may timeout loading
3. **MIME type**: Server may not recognize .mov files properly

### Immediate solutions:
```bash
# Test if videos load directly
curl -I http://localhost:8082/videos/import_model.mov

# Check file sizes
ls -lh docs/videos/

# Convert one video to test
ffmpeg -i docs/videos/import_model.mov -c:v libx264 -crf 23 docs/videos/import_model.mp4
```

---

## 📊 Storage Comparison

| Method | Cost | File Size Limit | Complexity | GitHub Pages |
|--------|------|-----------------|------------|--------------|
| Git LFS | $5/month after 1GB | 2GB | Medium | ✅ |
| Releases | Free | 2GB | Low | ❌ (external links) |
| YouTube | Free | 256GB | Low | ✅ (embedded) |
| Optimized Files | Free | 100MB | Medium | ✅ |

## 🎯 Next Steps

1. **Immediate**: Convert MOV to MP4 for better compatibility
2. **Short-term**: Set up Git LFS for professional video storage
3. **Long-term**: Consider YouTube/Vimeo for public documentation

Choose the option that best fits your needs and budget!
