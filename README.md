# Report to Reveal - Backend MVP

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file (copy from env_example.txt):
```bash
# Copy the example file
copy env_example.txt .env

# Edit .env and add your OpenAI API key (optional but recommended)
OPENAI_API_KEY=your_api_key_here
```

### 3. Run the Backend
```bash
python main.py
```

The server will start at `http://localhost:8000`

### 4. Access the Web Interface
Open your browser and go to:
- **Upload Interface**: `http://localhost:8000/backend/static/index.html`
- **API Documentation**: `http://localhost:8000/docs`

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── env_example.txt        # Environment variables template
│
├── core/                  # Core business logic
│   ├── document_processor.py   # PDF processing
│   ├── compliance_engine.py    # Rules-based evaluation
│   ├── ai_analyzer.py          # GPT-4 integration
│   └── report_generator.py     # Word document generation
│
├── static/                # Web interface
│   └── index.html        # Upload interface
│
├── uploads/              # Uploaded PDF files (auto-created)
├── results/              # Generated reports (auto-created)
└── temp/                 # Temporary files (auto-created)
```

## 🔧 API Endpoints

### Document Upload
```bash
POST /api/v1/upload
```
Upload a single PDF for analysis

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@document.pdf" \
  -F "email=user@example.com"
```

### Get Analysis Results
```bash
GET /api/v1/analyze/{analysis_id}
```
Check the status and results of an analysis

### Download Report
```bash
GET /api/v1/report/{analysis_id}
```
Download the generated Word document report

### Batch Upload
```bash
POST /api/v1/batch
```
Upload multiple PDFs (max 5) for batch processing

### Health Check
```bash
GET /health
```
Check if the backend is operational

## 🧪 Testing

### Run the Test Script
```bash
python test_backend.py
```

This will:
1. Upload a sample PDF
2. Wait for analysis to complete
3. Display the compliance score
4. Download the generated report

### Manual Testing with Web Interface
1. Open `backend/static/index.html` in your browser
2. Drag and drop a PDF file
3. Enter your email (optional)
4. Click "Upload and Analyze"
5. Wait for results
6. Download the Word report

## 📊 How It Works

### 1. Document Processing
- Extracts text using PyMuPDF
- Falls back to OCR for scanned PDFs
- Extracts tables and metrics
- Identifies parameters mentioned

### 2. Compliance Evaluation
Based on David Shackleton's requirements:

**Critical Parameters (Must Have):**
- Dissolved Oxygen (with depth profiles)
- Orthophosphate (below oxycline)
- Ammonia (in hypoxic water)
- Phytoplankton Taxonomy (with biovolume)
- Bathymetry (for calculations)

**Problematic Parameters (Red Flags):**
- Conductivity, pH (not actionable)
- Chlorophyll-a (masks cyanobacteria)
- Trophic State Index (outdated)
- Secchi Disk (symptomatic)

### 3. Scoring System
- **+10 points** for each critical parameter present
- **-10 points** for each critical parameter missing
- **+15 points** for each critical calculation performed
- **-15 points** for each critical calculation missing
- **-5 points** for each problematic parameter present

### 4. AI Enhancement (if OpenAI configured)
- Analyzes if report focuses on symptoms vs. root causes
- Checks parameter measurement quality
- Identifies counter-productive interventions
- Provides overall quality assessment

### 5. Report Generation
Creates a professional Word document with:
- Executive summary
- Compliance score card
- Parameter analysis
- Missing calculations
- Specific recommendations
- Call to action

## ⚙️ Configuration

### Compliance Rules
Edit `compliance_rules.json` to modify:
- Critical parameters and their requirements
- Problematic parameters to flag
- Scoring weights
- Red flag phrases

### OpenAI Integration (Optional)
Add your API key to `.env`:
```
OPENAI_API_KEY=sk-...
```

Without OpenAI:
- Basic keyword-based analysis still works
- No AI insights section in reports
- Slightly lower accuracy in detecting context

## 🔍 Monitoring

### Check System Status
```bash
GET /api/v1/status
```

Returns:
- Total analyses performed
- Current processing count
- Error count
- AI availability

### View Logs
The backend logs all operations. Check the console output for:
- Document processing steps
- Analysis progress
- Any errors

## 🚨 Troubleshooting

### "Module not found" Error
```bash
pip install -r requirements.txt
```

### OCR Not Working
Install Tesseract OCR:
```bash
# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Add to PATH or set in code:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Port Already in Use
Change the port in `.env`:
```
PORT=8001
```

### Large PDF Files Timing Out
Increase timeout in `test_backend.py`:
```python
async with httpx.AsyncClient(timeout=60.0) as client:
```

## 📈 Performance

- Typical analysis time: 10-30 seconds per document
- Memory usage: ~200MB base + document size
- Supports PDFs up to 50MB
- Can process 5 documents in parallel

## 🔐 Security Notes

For production deployment:
1. Change `SECRET_KEY` in `.env`
2. Add authentication to admin endpoints
3. Use PostgreSQL instead of SQLite
4. Add rate limiting
5. Validate file uploads more strictly
6. Use HTTPS

## 📝 Next Steps

1. **Test with your documents**: Run some real lake reports through the system
2. **Refine scoring**: Adjust weights based on results
3. **Add more parameters**: Expand the compliance rules as needed
4. **Deploy to cloud**: Consider AWS, Azure, or Google Cloud
5. **Add authentication**: Protect admin endpoints
6. **Build frontend**: Create a full React/Vue application

## 🤝 Support

For issues or questions about the backend:
1. Check the logs in the console
2. Verify all dependencies are installed
3. Ensure PDFs are valid and not corrupted
4. Check that OpenAI API key is valid (if using)

## 📄 License

This MVP is provided as-is for the Report to Reveal project.

---

**Built for David Cates by the Report to Reveal development team**
