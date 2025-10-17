# SimExR Documentation Site

This directory contains the complete documentation for the SimExR (Simulation Execution and Reasoning) framework.

## 🌐 Live Documentation

The documentation is designed to be deployed as a GitHub Pages site. You can view it locally or deploy it to GitHub Pages.

### Local Development

To test the documentation locally:

```bash
# Start local server
cd docs
python3 -m http.server 8080

# View in browser
open http://localhost:8080/test.html
```

### GitHub Pages Deployment

1. **Enable GitHub Pages** in your repository settings
2. **Set source** to "GitHub Actions" 
3. **Push changes** to the main branch
4. **GitHub Actions** will automatically build and deploy

## 📁 File Structure

```
docs/
├── index.md                    # Main documentation index (Markdown)
├── test.html                   # Interactive HTML version
├── diagrams.html              # Architecture diagrams
├── COMPLETE_DOCUMENTATION.md   # Comprehensive guide
├── API_REFERENCE.md           # Detailed API documentation
├── QUICK_START.md             # Getting started guide
├── EXAMPLES.md                # Real-world examples
├── _config.yml                # Jekyll configuration
├── Gemfile                    # Ruby dependencies
└── .github/workflows/docs.yml # GitHub Actions workflow
```

## 🎯 Documentation Pages

### Main Pages
- **[test.html](test.html)** - Interactive documentation homepage
- **[diagrams.html](diagrams.html)** - Architecture diagrams and visualizations
- **[index.md](index.md)** - Markdown version of main page

### Content Pages
- **[COMPLETE_DOCUMENTATION.md](COMPLETE_DOCUMENTATION.md)** - Full framework documentation
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API reference
- **[QUICK_START.md](QUICK_START.md)** - Installation and setup guide
- **[EXAMPLES.md](EXAMPLES.md)** - Examples and demonstrations

## 🚀 Features

### Interactive Elements
- **Mermaid Diagrams** - Architecture and workflow visualizations
- **Responsive Design** - Works on desktop and mobile
- **Navigation** - Easy navigation between sections
- **Code Examples** - Syntax-highlighted code blocks

### Content Coverage
- **Complete Architecture** - System design and components
- **API Documentation** - All endpoints with examples
- **Workflow Diagrams** - Step-by-step process flows
- **Real Examples** - Van der Pol, Lorenz, custom models
- **Deployment Guide** - Production deployment strategies

## 🔧 Customization

### Styling
Edit the CSS in `test.html` and `diagrams.html` to customize appearance.

### Content
- Update Markdown files for content changes
- Modify HTML files for layout changes
- Add new diagrams using Mermaid syntax

### Jekyll Configuration
Edit `_config.yml` to customize Jekyll settings for GitHub Pages.

## 📊 Diagrams

The documentation includes comprehensive diagrams:

1. **System Architecture** - Complete component overview
2. **Workflow Sequence** - End-to-end process flow
3. **FastAPI Details** - API architecture specifics
4. **Data Flow** - Information processing pipeline
5. **Deployment Architecture** - Production deployment setup

## 🎨 Visual Design

### Color Scheme
- **Primary Blue**: #0366d6 (GitHub blue)
- **Success Green**: #28a745
- **Warning Yellow**: #ffd33d
- **Danger Orange**: #f66a0a
- **Background**: #f8f9fa

### Typography
- **Font Family**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto
- **Responsive Design**: Grid layouts with mobile support
- **Accessibility**: High contrast and readable fonts

## 🚀 Deployment Instructions

### For GitHub Pages

1. **Repository Settings**:
   - Go to Settings → Pages
   - Source: "Deploy from a branch" or "GitHub Actions"
   - Branch: main
   - Folder: /docs

2. **Custom Domain** (optional):
   - Add CNAME file with your domain
   - Configure DNS settings

3. **SSL Certificate**:
   - Automatically provided by GitHub Pages
   - Custom domains may need additional setup

### For Custom Hosting

1. **Static Site Hosting**:
   - Upload all files to web server
   - Ensure proper MIME types for .md files
   - Configure redirects if needed

2. **CDN Integration**:
   - Use CloudFlare or similar for performance
   - Enable compression and caching
   - Set up SSL certificates

## 🔍 Testing

### Local Testing
```bash
# Test all pages
curl http://localhost:8080/test.html
curl http://localhost:8080/diagrams.html
curl http://localhost:8080/index.md

# Check for broken links
# (Use link checker tool of your choice)
```

### Validation
- **HTML Validation**: Use W3C HTML validator
- **Accessibility**: Test with screen readers
- **Mobile**: Test responsive design on various devices
- **Performance**: Check loading times and optimization

## 📈 Analytics

Consider adding analytics to track documentation usage:

- **Google Analytics**: Add tracking code to HTML files
- **GitHub Insights**: Use repository insights for basic metrics
- **Custom Analytics**: Implement custom tracking if needed

## 🤝 Contributing

To contribute to the documentation:

1. **Fork** the repository
2. **Edit** documentation files
3. **Test** changes locally
4. **Submit** pull request with description

### Content Guidelines
- Use clear, concise language
- Include code examples where helpful
- Maintain consistent formatting
- Update diagrams when architecture changes

---

**SimExR Documentation** - Comprehensive guide for the Simulation Execution and Reasoning framework.
