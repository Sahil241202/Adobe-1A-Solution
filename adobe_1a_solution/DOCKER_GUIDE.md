# Docker Guide for Adobe Challenge 1A

This guide provides comprehensive instructions for building and running the PDF Outline Extractor using Docker.

## 🚀 Quick Start

### Prerequisites
- Docker installed on your system
- Docker Compose (usually included with Docker Desktop)

### Option 1: Using Docker Compose (Recommended)

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

### Option 2: Using Docker Commands

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

## 📁 Directory Structure

```
adobe_1a_solution/
├── input/          # Place your PDF files here
├── output/         # Generated JSON files will appear here
├── logs/           # Application logs (optional)
├── Dockerfile      # Container definition
├── docker-compose.yml
└── .dockerignore   # Files to exclude from build
```

## 🔧 Configuration Options

### Environment Variables

You can customize the behavior using environment variables:

```yaml
# In docker-compose.yml
environment:
  - PYTHONUNBUFFERED=1
  - PYTHONDONTWRITEBYTECODE=1
  - LOG_LEVEL=INFO
```

### Volume Mounts

- **Input**: Read-only mount for PDF files
- **Output**: Write access for generated JSON files
- **Logs**: Optional mount for application logs

## 🛠️ Development Mode

For development with hot reload:

```bash
# Run development service
docker-compose --profile dev up pdf-extractor-dev

# Or build and run manually
docker build --target builder -t adobe-challenge-1a:dev .
docker run -v $(pwd)/input:/app/input:ro \
           -v $(pwd)/output:/app/output \
           -v $(pwd)/pdf_extractor:/app/pdf_extractor \
           adobe-challenge-1a:dev
```

## 📊 Monitoring and Health Checks

The container includes health checks:

```bash
# Check container health
docker ps

# View health check logs
docker inspect pdf-outline-extractor | grep -A 10 Health
```

## 🔍 Troubleshooting

### Common Issues

1. **No PDF files found:**
   ```bash
   # Ensure PDF files are in the input directory
   ls input/*.pdf
   ```

2. **Permission issues:**
   ```bash
   # Fix directory permissions
   chmod 755 input output
   ```

3. **Container won't start:**
   ```bash
   # Check container logs
   docker logs pdf-outline-extractor
   ```

4. **Build failures:**
   ```bash
   # Clean build cache
   docker system prune -a
   docker-compose build --no-cache
   ```

### Debug Mode

Run with verbose logging:

```bash
docker-compose run --rm pdf-extractor python main.py --verbose
```

## 🧹 Cleanup

### Remove containers and images:
```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi adobe-challenge-1a:latest

# Clean up all unused resources
docker system prune -a
```

### Remove generated files:
```bash
# Clean output directory
rm -rf output/*.json

# Clean logs
rm -rf logs/*
```

## 📋 Best Practices

1. **Always use specific image tags** for production
2. **Mount volumes** instead of copying files into the image
3. **Use multi-stage builds** to reduce image size
4. **Run as non-root user** for security
5. **Include health checks** for monitoring
6. **Use .dockerignore** to exclude unnecessary files

## 🔒 Security Considerations

- Container runs as non-root user (`appuser`)
- Input directory is mounted as read-only
- Minimal runtime dependencies
- No unnecessary build tools in final image

## 📈 Performance Optimization

- Multi-stage build reduces final image size
- Layer caching optimizes build times
- Minimal base image (python:3.9-slim)
- Efficient dependency installation

## 🎯 Challenge Requirements Compliance

✅ **Platform**: linux/amd64  
✅ **Size**: <200MB total  
✅ **Offline**: No external dependencies  
✅ **Production-ready**: Security and best practices implemented  

## 📞 Support

For issues related to:
- **Docker setup**: Check this guide and troubleshooting section
- **Application logic**: Refer to the main README.md
- **Challenge requirements**: Review the challenge documentation
