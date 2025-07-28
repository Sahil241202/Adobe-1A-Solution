# PDF Outline Extractor - Challenge 1A Solution

## 🚀 Quick Start Guide

### **Prerequisites**
- Docker installed on your system
- Docker Compose (usually included with Docker Desktop)

### **Option 1: Docker (Recommended - Easiest)**

1. **Clone and navigate to the project:**
   ```bash
   cd adobe_1a_solution
   ```

2. **Add your PDF files to the input directory:**
   ```bash
   # Copy your PDF files to the input folder
   cp /path/to/your/pdfs/*.pdf input/
   ```

3. **Build and run the container:**
   ```bash
   docker-compose up --build
   ```

4. **Check the results:**
   ```bash
   # View generated JSON files
   ls output/
   ```

### **Option 2: Docker Commands (Alternative)**

1. **Build the image:**
   ```bash
   docker build -t adobe-challenge-1a .
   ```

2. **Run the container:**
   ```bash
   docker run -v $(pwd)/input:/app/input:ro \
              -v $(pwd)/output:/app/output \
              adobe-challenge-1a
   ```

### **Option 3: Local Python Development**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run with default input folder:**
   ```bash
   python main.py
   ```

3. **Run with custom folder:**
   ```bash
   python main.py docs/
   python main.py C:/MyDocuments/PDFs/
   ```

---

## 🎯 Challenge 1A - Docker Solution

### **What It Does**

This solution extracts structured outlines (headings H1, H2, H3) from PDF documents using a font-based analysis approach with comprehensive bias mitigation:

#### **1. Font Statistics Analysis**
- Analyzes font sizes, styles, and characteristics across the document
- Establishes baseline statistics and calculates document-adaptive thresholds
- Uses statistical clustering with percentile analysis

#### **2. Adaptive Threshold Detection** 
Instead of fixed thresholds, the system calculates document-specific heading thresholds based on:
- Mean and median font sizes of the document
- Font variety and size distribution patterns
- Document complexity classification (simple forms vs complex technical documents)
- Per-document H3 threshold: `max(mean_font * 0.85, 8.0)` for fairness

#### **3. Confidence-Based Classification**
Each text block receives a confidence score (0-1) based on:
- **Font size**: Relative to document baseline with adaptive scaling
- **Font weight**: Bold detection via font flags and naming patterns  
- **Structural patterns**: Numbered sections, capitalization, title case
- **Position context**: Page location and surrounding text analysis
- **Language fairness**: +0.15 boost for non-ASCII characters to ensure equal treatment

#### **4. Bias Mitigation & Fairness**
Active measures to ensure fair treatment across:
- **Document types**: Forms, manuals, flyers, technical documents
- **Multiple languages**: Unicode support with bias compensation for non-English text
- **Font characteristics**: Adaptive thresholds prevent size-based discrimination
- **Content types**: Balanced filtering without over-aggressive removal

### **Models and Libraries Used**

- **PyMuPDF (fitz) v1.23.26**: Core PDF parsing and text extraction (~50MB)
- **NumPy v1.24.3**: Statistical analysis for font clustering and percentile calculations (~15MB)
- **No external ML models**: Pure algorithmic approach keeps total deployment size <200MB
- **No internet dependencies**: Fully offline operation as required

### **Key Performance Features**

- ⚡ **Fast Processing**: <10 seconds for 50-page PDFs (typically <1 second per PDF)
- 🌍 **Language Support**: Unicode-aware processing with bias compensation  
- 🎯 **High Accuracy**: Adaptive thresholds reduce false positives/negatives
- 🧹 **Smart Filtering**: Removes form fields, metadata, decorative elements
- 🔄 **Adaptive Processing**: Automatically adjusts to document characteristics

---

## 📁 **Project Structure & Output Format**

### **Directory Structure**
```
adobe_1a_solution/
├── input/              # Place your PDF files here
├── output/             # Generated JSON files appear here
├── pdf_extractor/      # Core extraction modules
├── main.py            # Local development entry point
├── docker_entrypoint.py # Docker entry point
├── Dockerfile         # Container definition
├── docker-compose.yml # Docker orchestration
└── requirements.txt   # Python dependencies
```

### **Challenge 1A Output Format**

Each PDF generates a corresponding JSON file with:
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1|H2|H3", 
      "text": "Heading Text",
      "page": 0
    }
  ]
}
```

---

## 🧪 **Testing Examples**

### **Docker Testing (Recommended)**

**Quick Test with Sample Files:**
```bash
# The project comes with sample PDF files in input/
# Just run the container to process them
docker-compose up --build

# Check results
ls output/  # Should contain file01.json, file02.json, etc.
```

**Test with Your Own PDFs:**
```bash
# Add your PDF files
cp /path/to/your/pdfs/*.pdf input/

# Run the container
docker run -v $(pwd)/input:/app/input:ro \
           -v $(pwd)/output:/app/output \
           adobe-challenge-1a

# View results
cat output/yourfile.json
```

### **Local Development Testing**

```bash
# Process all PDFs in input folder
python main.py

# Process single PDF file  
python main.py document.pdf

# Process with detailed progress
python main.py --verbose

# Process with fast parallel processing
python main.py --fast
```

---

## 🔧 **Advanced Usage**

### **Docker Compose Options**

**Development mode with hot reload:**
```bash
docker-compose --profile dev up pdf-extractor-dev
```

**Run in background:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

### **Environment Variables**

You can customize behavior using environment variables:
```yaml
# In docker-compose.yml
environment:
  - PYTHONUNBUFFERED=1
  - PYTHONDONTWRITEBYTECODE=1
  - LOG_LEVEL=INFO
```

### **Volume Mounts**

- **Input**: Read-only mount for PDF files (`./input:/app/input:ro`)
- **Output**: Write access for generated JSON files (`./output:/app/output`)
- **Logs**: Optional mount for application logs (`./logs:/app/logs`)

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**No PDF files found:**
```bash
# Ensure PDF files are in the input directory
ls input/*.pdf
```

**Permission issues:**
```bash
# Fix directory permissions
chmod 755 input output
```

**Container won't start:**
```bash
# Check container logs
docker logs pdf-outline-extractor
```

**Build failures:**
```bash
# Clean build cache
docker system prune -a
docker-compose build --no-cache
```

### **Debug Mode**

Run with verbose logging:
```bash
docker-compose run --rm pdf-extractor python main.py --verbose
```

---

## 🧹 **Cleanup**

### **Remove containers and images:**
```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi adobe-challenge-1a:latest

# Clean up all unused resources
docker system prune -a
```

### **Remove generated files:**
```bash
# Clean output directory
rm -rf output/*.json

# Clean logs
rm -rf logs/*
```

---

## 🔧 **Technical Requirements Met**

- ✅ **CPU Architecture**: AMD64 (x86_64) compatible
- ✅ **No GPU Dependencies**: Pure CPU processing
- ✅ **Model Size**: <200MB total (no ML models used)
- ✅ **Offline Operation**: No network/internet calls
- ✅ **Performance**: ≤10 seconds for 50-page PDFs
- ✅ **Platform**: linux/amd64 Docker containers

## 🏗️ **Architecture Highlights**

- **Adaptive Processing**: No hardcoded thresholds or file-specific logic
- **Bias Mitigation**: Fair treatment across document types and languages  
- **Modular Design**: Reusable components for Round 1B extension
- **Performance Optimized**: Efficient font analysis with statistical clustering
- **Schema Compliant**: Exact JSON format as specified in challenge

---

## **Ready for Challenge 1A Submission! 🎉**

This solution meets all technical requirements while maintaining high accuracy and performance across diverse PDF document types.
