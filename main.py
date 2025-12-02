"""
FastAPI backend for Report to Reveal document analysis system
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import shutil
from pathlib import Path
import uuid
from datetime import datetime
import json
import logging

# Import core modules
from config import settings
from core.document_processor import DocumentProcessor
from core.compliance_engine import ComplianceEngine, ComplianceReport
from core.ai_analyzer import AIEnhancedCompliance
from core.report_generator import ReportGenerator
from core.email_service import initialize_email_service
from core.lake_assessment import LakeAssessment
from core.lake_assessment_report import LakeAssessmentReportGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered lake management report analysis system"
)

# Add CORS middleware with support for Vercel and ngrok
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://document-parsing-frontend-git-main-content-generation.vercel.app",
        "https://document-parsing-frontend-cdalywdww-content-generation.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.ngrok-free\.dev|https://.*\.ngrok\.io",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize components
document_processor = DocumentProcessor()
compliance_engine = ComplianceEngine()
ai_enhanced = AIEnhancedCompliance()
report_generator = ReportGenerator()
lake_assessment = LakeAssessment()
lake_assessment_report = LakeAssessmentReportGenerator()

# Initialize email service
email_service = initialize_email_service(settings)

# In-memory storage for demo (replace with database in production)
analysis_results = {}
# Meta-analysis storage - retain all uploaded plans as per Brief
meta_analysis_data = {
    "total_reports_analyzed": 0,
    "common_missing_parameters": {},
    "common_problematic_parameters": {},
    "average_compliance_score": 0,
    "all_analyses": []
}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "endpoints": {
            "upload": "/api/v1/upload",
            "analyze": "/api/v1/analyze/{analysis_id}",
            "report": "/api/v1/report/{analysis_id}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "document_processor": "operational",
            "compliance_engine": "operational",
            "ai_analyzer": "operational" if settings.openai_api_key else "not configured",
            "report_generator": "operational"
        }
    }

@app.post(f"{settings.api_prefix}/upload-single")  # Changed path to avoid conflict
async def upload_single_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_ocr: bool = False,
    email: Optional[str] = None
):
    """
    Legacy single file upload endpoint (kept for backward compatibility)
    
    Returns analysis_id for tracking
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Check file size
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {settings.max_upload_size / 1024 / 1024}MB"
        )
    
    # Generate unique ID for this analysis
    analysis_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_path = settings.upload_dir / f"{analysis_id}_{file.filename}"
    with open(upload_path, "wb") as f:
        f.write(contents)
    
    # Store initial result
    analysis_results[analysis_id] = {
        "id": analysis_id,
        "filename": file.filename,
        "upload_time": datetime.now().isoformat(),
        "email": email,
        "status": "processing",
        "file_path": str(upload_path),
        "document_type": "report"  # Default to report for legacy uploads
    }
    
    # Process in background - default to report type
    background_tasks.add_task(
        process_document_with_type,
        analysis_id,
        str(upload_path),
        "report"
    )
    
    return {
        "analysis_id": analysis_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Document uploaded successfully. Processing in background."
    }

async def process_document_background(analysis_id: str, file_path: str, use_ocr: bool):
    """Background task to process document"""
    try:
        logger.info(f"Starting background processing for {analysis_id}")
        
        # Update status
        analysis_results[analysis_id]["status"] = "extracting"
        
        # Step 1: Process document
        doc_data = await document_processor.process_document(file_path, use_ocr)
        analysis_results[analysis_id]["extraction_complete"] = True
        
        # Step 2: Compliance evaluation
        analysis_results[analysis_id]["status"] = "evaluating"
        compliance_eval = compliance_engine.evaluate_document(doc_data)
        
        # Step 3: AI analysis (if configured and not skipped)
        if settings.openai_api_key and not settings.skip_ai_analysis:
            analysis_results[analysis_id]["status"] = "ai_analysis"
            enhanced_eval = await ai_enhanced.enhanced_evaluation(doc_data, compliance_eval)
        else:
            enhanced_eval = compliance_eval
            if settings.skip_ai_analysis:
                logger.info(f"AI analysis skipped for {analysis_id} (skip_ai_analysis=True)")
        
        # Step 4: Generate report
        analysis_results[analysis_id]["status"] = "generating_report"
        report_path, summary_path = await report_generator.generate_report(
            doc_data,
            enhanced_eval,
            enhanced_eval.get("ai_insights"),
            output_path=settings.results_dir / f"{analysis_id}_report.docx",
            generate_summary=True
        )
        
        # Update final results
        analysis_results[analysis_id].update({
            "status": "complete",
            "completion_time": datetime.now().isoformat(),
            "compliance_score": enhanced_eval["compliance_percentage"],
            "compliance_level": enhanced_eval["compliance_level"].value,
            "document_data": doc_data,
            "evaluation": enhanced_eval,
            "report_path": report_path,
            "summary_path": summary_path
        })
        
        # Store for meta-analysis as per Brief requirement
        meta_analysis_data["all_analyses"].append({
            "analysis_id": analysis_id,
            "filename": analysis_results[analysis_id]["filename"],
            "date": datetime.now().isoformat(),
            "score": enhanced_eval["compliance_percentage"],
            "missing_parameters": enhanced_eval["critical_parameters"]["missing"],
            "problematic_parameters": enhanced_eval["problematic_parameters"]["found"]
        })
        
        # Update meta-analysis statistics
        meta_analysis_data["total_reports_analyzed"] += 1
        all_scores = [a["score"] for a in meta_analysis_data["all_analyses"]]
        meta_analysis_data["average_compliance_score"] = sum(all_scores) / len(all_scores)
        
        logger.info(f"Processing complete for {analysis_id}")
        
    except Exception as e:
        logger.error(f"Error processing document {analysis_id}: {e}")
        analysis_results[analysis_id].update({
            "status": "error",
            "error": str(e),
            "error_time": datetime.now().isoformat()
        })

async def process_document_with_type(analysis_id: str, file_path: str, document_type: str = None):
    """
    Process document using hybrid analysis approach.
    
    The system now automatically detects the document type and analyzes it
    BOTH as a retrospective report AND as a forward-looking plan, since
    most lake documents are hybrids of both.
    """
    try:
        logger.info(f"Starting hybrid processing for {analysis_id}")
        
        # Update status
        analysis_results[analysis_id]["status"] = "extracting"
        
        # Step 1: Process document
        doc_data = await document_processor.process_document(file_path, False)
        analysis_results[analysis_id]["extraction_complete"] = True
        
        # Step 2: AI-powered document type detection (if AI available)
        detected_type = None
        if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here" and not settings.skip_ai_analysis:
            analysis_results[analysis_id]["status"] = "detecting_type"
            try:
                ai_analyzer = ai_enhanced.ai_analyzer
                context = ai_analyzer._prepare_context(doc_data)
                detected_type = await ai_analyzer._detect_document_type(context)
                logger.info(f"AI detected document type: {detected_type.get('primary_type', 'hybrid')} "
                           f"(Plan: {detected_type.get('plan_percentage', 50)}%, "
                           f"Report: {detected_type.get('report_percentage', 50)}%)")
            except Exception as e:
                logger.warning(f"Document type detection failed, using hybrid: {e}")
                detected_type = {"primary_type": "hybrid", "plan_percentage": 50, "report_percentage": 50}
        
        # Step 3: Hybrid Compliance evaluation (analyzes as both plan AND report)
        analysis_results[analysis_id]["status"] = "evaluating"
        
        # Always use hybrid evaluation to analyze both aspects
        compliance_eval = compliance_engine.evaluate_hybrid(doc_data, detected_type)
        compliance_eval['evaluation_type'] = 'Hybrid Analysis (Plan + Report)'
        compliance_eval['detected_document_type'] = detected_type
        
        # Determine the dominant type based on percentages (consistent threshold)
        if detected_type:
            plan_pct = detected_type.get('plan_percentage', 50)
            report_pct = detected_type.get('report_percentage', 50)
        else:
            # Fallback to compliance engine's detection
            hybrid_analysis = compliance_eval.get('hybrid_analysis', {})
            characteristics = hybrid_analysis.get('document_characteristics', {})
            plan_pct = characteristics.get('plan_percentage', 50)
            report_pct = characteristics.get('report_percentage', 50)
        
        # Apply consistent threshold for determining dominant type
        # >70% means it's primarily one type, otherwise hybrid
        if report_pct > 70:
            dominant_type = 'report'
            dominant_label = f'Primarily Report ({report_pct}%)'
        elif plan_pct > 70:
            dominant_type = 'plan'
            dominant_label = f'Primarily Plan ({plan_pct}%)'
        else:
            dominant_type = 'hybrid'
            dominant_label = f'Hybrid (Report: {report_pct}%, Plan: {plan_pct}%)'
        
        logger.info(f"Document classification: {dominant_label}")
        
        compliance_eval['document_type'] = dominant_type
        compliance_eval['document_type_label'] = dominant_label
        compliance_eval['type_breakdown'] = {
            'plan_percentage': plan_pct,
            'report_percentage': report_pct,
            'dominant_type': dominant_type,
            'analysis_approach': 'Analyzed as both retrospective report and forward-looking plan'
        }
        
        # Also sync to doc_data for report generators that read from there
        doc_data['document_type'] = dominant_type
        doc_data['type_breakdown'] = compliance_eval['type_breakdown']
        
        # Step 4: Enhanced AI analysis (if configured and not skipped)
        if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here" and not settings.skip_ai_analysis:
            analysis_results[analysis_id]["status"] = "ai_analysis"
            enhanced_eval = await ai_enhanced.enhanced_evaluation(doc_data, compliance_eval)
        else:
            enhanced_eval = compliance_eval
            if settings.skip_ai_analysis:
                logger.info(f"AI analysis skipped for {analysis_id} (skip_ai_analysis=True)")
        
        # Step 4: Generate report
        analysis_results[analysis_id]["status"] = "generating_report"
        report_path, summary_path = await report_generator.generate_report(
            doc_data,
            enhanced_eval,
            enhanced_eval.get("ai_insights"),
            output_path=settings.results_dir / f"{analysis_id}_report.docx",
            generate_summary=True
        )
        
        # Update final results
        analysis_results[analysis_id].update({
            "status": "complete",
            "completion_time": datetime.now().isoformat(),
            "document_type": document_type,
            "compliance_score": enhanced_eval["compliance_percentage"],
            "compliance_level": enhanced_eval["compliance_level"].value,
            "document_data": doc_data,
            "evaluation": enhanced_eval,
            "report_path": report_path,
            "summary_path": summary_path
        })
        
        # Store for meta-analysis
        meta_analysis_data["all_analyses"].append({
            "analysis_id": analysis_id,
            "filename": analysis_results[analysis_id]["filename"],
            "document_type": document_type,
            "date": datetime.now().isoformat(),
            "score": enhanced_eval["compliance_percentage"],
            "missing_parameters": enhanced_eval["critical_parameters"]["missing"],
            "problematic_parameters": enhanced_eval["problematic_parameters"]["found"]
        })
        
        # Update meta-analysis statistics
        meta_analysis_data["total_reports_analyzed"] += 1
        all_scores = [a["score"] for a in meta_analysis_data["all_analyses"]]
        meta_analysis_data["average_compliance_score"] = sum(all_scores) / len(all_scores)
        
        logger.info(f"Processing complete for {analysis_id} ({document_type})")
        
        # Send email notifications if configured
        if email_service.is_configured():
            # Get contact info from analysis results
            contact_info = analysis_results[analysis_id].get("contact_info", {})
            
            # Send report to customer if automatic sending is enabled
            if settings.send_reports_automatically and contact_info.get("email"):
                # Send the summary report to customers (detailed report kept internal)
                report_to_send = Path(summary_path) if summary_path else Path(report_path)
                email_sent = email_service.send_report_to_customer(
                    to_email=contact_info["email"],
                    customer_name=contact_info.get("name", "Customer"),
                    report_path=report_to_send,
                    document_name=analysis_results[analysis_id]["filename"],
                    compliance_score=enhanced_eval["compliance_percentage"],
                    document_type=document_type
                )
                
                if email_sent:
                    logger.info(f"Report sent to {contact_info['email']}")
                    analysis_results[analysis_id]["email_sent"] = True
                    analysis_results[analysis_id]["email_sent_time"] = datetime.now().isoformat()
                else:
                    logger.warning(f"Failed to send report to {contact_info['email']}")
                    analysis_results[analysis_id]["email_sent"] = False
            
            # Always send admin notification when processing is complete
            email_service.send_processing_complete_notification(
                submission_id=analysis_results[analysis_id].get("submission_id", analysis_id),
                document_name=analysis_results[analysis_id]["filename"],
                compliance_score=enhanced_eval["compliance_percentage"],
                report_path=Path(report_path)
            )
        else:
            logger.info("Email service not configured. Skipping email notifications.")
        
    except Exception as e:
        logger.error(f"Error processing document {analysis_id}: {e}")
        analysis_results[analysis_id].update({
            "status": "error",
            "error": str(e),
            "error_time": datetime.now().isoformat()
        })

@app.get(f"{settings.api_prefix}/analyze/{{analysis_id}}")
async def get_analysis(analysis_id: str):
    """Get analysis results by ID"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[analysis_id]
    
    # Don't send full document data in response (too large)
    response = {
        "id": result["id"],
        "filename": result["filename"],
        "status": result["status"],
        "upload_time": result["upload_time"]
    }
    
    if result["status"] == "complete":
        response.update({
            "completion_time": result["completion_time"],
            "compliance_score": result["compliance_score"],
            "compliance_level": result["compliance_level"],
            "summary": ComplianceReport.generate_summary(result["evaluation"]),
            "recommendations": result["evaluation"]["recommendations"][:5],  # Top 5
            "report_available": True
        })
    elif result["status"] == "error":
        response.update({
            "error": result["error"],
            "error_time": result["error_time"]
        })
    
    return response

@app.get(f"{settings.api_prefix}/report/{{analysis_id}}")
async def download_report(analysis_id: str):
    """Download generated Word report"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[analysis_id]
    
    if result["status"] != "complete":
        raise HTTPException(
            status_code=400, 
            detail=f"Report not ready. Current status: {result['status']}"
        )
    
    report_path = Path(result["report_path"])
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        path=report_path,
        filename=f"analysis_{result['filename'].replace('.pdf', '')}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ============================================
# PUBLIC DOWNLOAD ENDPOINTS (No authentication required)
# ============================================

@app.get(f"{settings.api_prefix}/status/{{analysis_id}}")
async def get_analysis_status(analysis_id: str):
    """
    Get status of a specific analysis (public endpoint for download page)
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[analysis_id]
    
    # Check if report files are ready
    report_ready = False
    summary_ready = False
    
    if result.get("report_path"):
        report_ready = Path(result["report_path"]).exists()
    
    if result.get("summary_path"):
        summary_ready = Path(result["summary_path"]).exists()
    
    return {
        "analysis_id": analysis_id,
        "status": result["status"],
        "filename": result.get("filename", ""),
        "report_ready": report_ready,
        "summary_ready": summary_ready,
        "compliance_score": result.get("compliance_score"),
        "document_type": result.get("document_type", "auto")
    }

@app.get(f"{settings.api_prefix}/download/{{analysis_id}}/{{report_type}}")
async def download_public_report(analysis_id: str, report_type: str):
    """
    Download report files (public endpoint)
    
    Args:
        analysis_id: The analysis ID
        report_type: Either 'report' for full report or 'summary' for summary report
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[analysis_id]
    
    if result["status"] != "complete":
        raise HTTPException(
            status_code=400, 
            detail=f"Report not ready. Current status: {result['status']}"
        )
    
    # Determine which file to serve
    if report_type == "summary":
        file_path = result.get("summary_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Summary report not available")
        filename_suffix = "_summary"
    elif report_type == "report":
        file_path = result.get("report_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Full report not available")
        filename_suffix = "_report"
    else:
        raise HTTPException(status_code=400, detail="Invalid report type. Use 'report' or 'summary'")
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Create a user-friendly filename
    original_filename = result.get("filename", "document").replace('.pdf', '')
    download_filename = f"{original_filename}{filename_suffix}.docx"
    
    return FileResponse(
        path=file_path,
        filename=download_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get(f"{settings.api_prefix}/status")
async def get_system_status():
    """Get overall system status and statistics"""
    total_analyses = len(analysis_results)
    complete = sum(1 for r in analysis_results.values() if r["status"] == "complete")
    processing = sum(1 for r in analysis_results.values() if r["status"] == "processing")
    errors = sum(1 for r in analysis_results.values() if r["status"] == "error")
    
    return {
        "system_status": "operational",
        "statistics": {
            "total_analyses": total_analyses,
            "complete": complete,
            "processing": processing,
            "errors": errors
        },
        "ai_enabled": bool(settings.openai_api_key),
        "compliance_rules_version": "1.0",
        "server_time": datetime.now().isoformat()
    }

@app.post(f"{settings.api_prefix}/send-report/{{analysis_id}}")
async def send_report_email(analysis_id: str):
    """Manually send report to customer email"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[analysis_id]
    
    if result["status"] != "complete":
        raise HTTPException(status_code=400, detail="Analysis not complete")
    
    if not email_service.is_configured():
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    contact_info = result.get("contact_info", {})
    if not contact_info.get("email"):
        raise HTTPException(status_code=400, detail="No email address available")
    
    # Send the summary report to customers (detailed report kept internal)
    report_to_send = Path(result.get("summary_path", result["report_path"]))
    email_sent = email_service.send_report_to_customer(
        to_email=contact_info["email"],
        customer_name=contact_info.get("name", "Customer"),
        report_path=report_to_send,
        document_name=result["filename"],
        compliance_score=result["evaluation"]["compliance_percentage"],
        document_type=result.get("document_type", "report")
    )
    
    if email_sent:
        analysis_results[analysis_id]["email_sent"] = True
        analysis_results[analysis_id]["email_sent_time"] = datetime.now().isoformat()
        return {"success": True, "message": f"Report sent to {contact_info['email']}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")

@app.get(f"{settings.api_prefix}/email-status")
async def check_email_configuration():
    """Check if email service is configured"""
    return {
        "configured": email_service.is_configured(),
        "smtp_host": settings.smtp_host if settings.smtp_host else "Not configured",
        "automatic_sending": settings.send_reports_automatically,
        "admin_email": settings.admin_email if settings.admin_email else "Not configured"
    }

@app.post(f"{settings.api_prefix}/trend-analysis")
async def generate_trend_analysis(
    submission_id: str,
    analysis_ids: List[str] = None
):
    """
    Generate trend analysis for multiple years of reports
    This creates a Lake Assessment showing trends over time
    """
    from core.summary_generator import summary_generator
    
    # Collect data for trend analysis
    multi_year_data = []
    
    if analysis_ids:
        # Use specific analysis IDs
        for aid in analysis_ids:
            if aid in analysis_results and analysis_results[aid]["status"] == "complete":
                result = analysis_results[aid]
                multi_year_data.append({
                    "year": result.get("upload_time", "Unknown")[:4],  # Extract year
                    "compliance_percentage": result.get("compliance_score", 0),
                    "critical_parameters": result.get("evaluation", {}).get("critical_parameters", {}),
                    "filename": result.get("filename", "Unknown")
                })
    else:
        # Use all analyses for a submission
        for aid, result in analysis_results.items():
            if result.get("submission_id") == submission_id and result["status"] == "complete":
                multi_year_data.append({
                    "year": result.get("upload_time", "Unknown")[:4],
                    "compliance_percentage": result.get("compliance_score", 0),
                    "critical_parameters": result.get("evaluation", {}).get("critical_parameters", {}),
                    "filename": result.get("filename", "Unknown")
                })
    
    if len(multi_year_data) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 years of data for trend analysis"
        )
    
    # Sort by year
    multi_year_data.sort(key=lambda x: x.get("year", "0"))
    
    # Generate trend summary
    try:
        trend_report_path = summary_generator.generate_trend_summary(
            multi_year_data=multi_year_data,
            output_path=settings.results_dir / f"trend_analysis_{submission_id}.docx"
        )
        
        return {
            "success": True,
            "message": f"Trend analysis generated for {len(multi_year_data)} reports",
            "report_path": trend_report_path,
            "years_analyzed": [d["year"] for d in multi_year_data]
        }
    except Exception as e:
        logger.error(f"Failed to generate trend analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.api_prefix}/meta-analysis")
async def get_meta_analysis():
    """Get meta-analysis of all uploaded Lake Management Plans (as per Brief requirement)"""
    
    # Calculate most common missing parameters
    missing_params_count = {}
    problematic_params_count = {}
    
    for analysis in meta_analysis_data["all_analyses"]:
        for param in analysis.get("missing_parameters", []):
            param_name = param.get("name", param) if isinstance(param, dict) else param
            missing_params_count[param_name] = missing_params_count.get(param_name, 0) + 1
        
        for param in analysis.get("problematic_parameters", []):
            problematic_params_count[param] = problematic_params_count.get(param, 0) + 1
    
    # Sort by frequency
    most_missing = sorted(missing_params_count.items(), key=lambda x: x[1], reverse=True)[:5]
    most_problematic = sorted(problematic_params_count.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_reports_analyzed": meta_analysis_data["total_reports_analyzed"],
        "average_compliance_score": round(meta_analysis_data["average_compliance_score"], 1) if meta_analysis_data["total_reports_analyzed"] > 0 else 0,
        "most_commonly_missing_parameters": [{"parameter": p[0], "frequency": p[1]} for p in most_missing],
        "most_common_problematic_parameters": [{"parameter": p[0], "frequency": p[1]} for p in most_problematic],
        "recent_analyses": meta_analysis_data["all_analyses"][-10:],  # Last 10
        "insights": {
            "trend": "Most reports focus on symptoms rather than root causes",
            "main_issue": "Lack of hypoxic volume calculations and DO profiling",
            "recommendation": "Industry needs education on importance of bathymetry and DO dynamics"
        }
    }

@app.post(f"{settings.api_prefix}/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    contact_info: str = Form(...)
):
    """
    Upload documents for hybrid analysis.
    
    The system automatically detects document type and analyzes documents
    BOTH as retrospective reports AND forward-looking plans, since most
    lake management documents are hybrids of both.
    
    Document type selection is NO LONGER REQUIRED - the AI will figure it out.
    """
    import json
    
    # Parse contact info JSON
    try:
        contact_data = json.loads(contact_info)
    except:
        raise HTTPException(status_code=400, detail="Invalid contact information")
    
    # Validate required fields (email removed - users download reports directly)
    required_fields = ['name', 'organization']
    for field in required_fields:
        if not contact_data.get(field):
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Document type is now optional - AI will detect it
    # If provided, it's used as a hint but hybrid analysis is still performed
    document_type_hint = contact_data.get('documentType', 'auto')
    
    if len(files) > 3:
        raise HTTPException(
            status_code=400,
            detail="Maximum 3 documents allowed per submission"
        )
    
    submission_id = str(uuid.uuid4())
    analysis_ids = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            continue
        
        # Process each file
        analysis_id = str(uuid.uuid4())
        contents = await file.read()
        
        # Save file
        upload_path = settings.upload_dir / f"{analysis_id}_{file.filename}"
        with open(upload_path, "wb") as f:
            f.write(contents)
        
        # Store result - document type will be auto-detected
        analysis_results[analysis_id] = {
            "id": analysis_id,
            "submission_id": submission_id,
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "contact_info": contact_data,
            "document_type": "auto",  # Will be detected by AI
            "document_type_hint": document_type_hint,  # User hint if provided
            "status": "queued",
            "file_path": str(upload_path)
        }
        
        analysis_ids.append(analysis_id)
        
        # Add to background tasks - document type will be auto-detected
        background_tasks.add_task(
            process_document_with_type,
            analysis_id,
            str(upload_path),
            document_type_hint  # Pass hint, but hybrid analysis will be used
        )
    
    # Store metadata for trend analysis if multiple reports
    if len(analysis_ids) >= 3:
        meta_analysis_data[submission_id] = {
            "submission_id": submission_id,
            "document_type": "hybrid",  # All documents analyzed as hybrids
            "analysis_ids": analysis_ids,
            "contact_info": contact_data,
            "requires_trend_analysis": True
        }
        
        # Add background task to check for Lake Assessment opportunity
        background_tasks.add_task(
            check_and_trigger_assessment,
            submission_id
        )
        logger.info(f"Lake Assessment check scheduled for submission {submission_id}")
    
    # Send admin notification if email is configured
    if email_service.is_configured() and analysis_ids:
        document_names = [analysis_results[aid]["filename"] for aid in analysis_ids]
        email_service.send_admin_notification(
            customer_name=contact_data.get("name", "Unknown"),
            customer_email=contact_data.get("email", "Unknown"),
            organization=contact_data.get("organization", "Unknown"),
            document_names=document_names,
            submission_id=submission_id
        )
        logger.info(f"Admin notification sent for submission {submission_id}")
    
    return {
        "success": True,
        "submission_id": submission_id,
        "analysis_ids": analysis_ids,
        "files_processed": len(analysis_ids),
        "analysis_type": "hybrid",
        "message": f"{len(analysis_ids)} document(s) uploaded successfully. AI will analyze each as both a report and a plan."
    }

@app.post(f"{settings.api_prefix}/batch")
async def batch_upload_legacy(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    email: Optional[str] = None
):
    """Legacy batch upload endpoint - redirects to new endpoint with hybrid analysis"""
    # For backward compatibility - now uses hybrid analysis
    contact_info = json.dumps({
        "name": "Unknown",
        "email": email or "unknown@example.com",
        "organization": "Unknown"
        # documentType is no longer required - AI will auto-detect
    })
    
    return await upload_documents(background_tasks, files, contact_info)
    
    batch_id = str(uuid.uuid4())
    analysis_ids = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            continue
        
        # Process each file
        analysis_id = str(uuid.uuid4())
        contents = await file.read()
        
        # Save file
        upload_path = settings.upload_dir / f"{analysis_id}_{file.filename}"
        with open(upload_path, "wb") as f:
            f.write(contents)
        
        # Store result
        analysis_results[analysis_id] = {
            "id": analysis_id,
            "batch_id": batch_id,
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "email": email,
            "status": "queued",
            "file_path": str(upload_path)
        }
        
        analysis_ids.append(analysis_id)
        
        # Add to background tasks
        background_tasks.add_task(
            process_document_background,
            analysis_id,
            str(upload_path),
            False
        )
    
    return {
        "batch_id": batch_id,
        "analysis_ids": analysis_ids,
        "files_queued": len(analysis_ids),
        "message": "Batch processing started"
    }

@app.get(f"{settings.api_prefix}/batch/{{batch_id}}")
async def get_batch_status(batch_id: str):
    """Get status of batch processing"""
    batch_analyses = [
        r for r in analysis_results.values() 
        if r.get("batch_id") == batch_id
    ]
    
    if not batch_analyses:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return {
        "batch_id": batch_id,
        "total_files": len(batch_analyses),
        "complete": sum(1 for a in batch_analyses if a["status"] == "complete"),
        "processing": sum(1 for a in batch_analyses if a["status"] in ["processing", "queued"]),
        "errors": sum(1 for a in batch_analyses if a["status"] == "error"),
        "analyses": [
            {
                "id": a["id"],
                "filename": a["filename"],
                "status": a["status"],
                "compliance_score": a.get("compliance_score")
            }
            for a in batch_analyses
        ]
    }

# Admin endpoints (protected in production)
@app.get(f"{settings.api_prefix}/admin/rules")
async def get_compliance_rules():
    """Get current compliance rules (admin only)"""
    from config import COMPLIANCE_RULES
    return COMPLIANCE_RULES

@app.put(f"{settings.api_prefix}/admin/rules")
async def update_compliance_rules(rules: dict):
    """Update compliance rules (admin only)"""
    # In production, this would update the database
    # For now, just validate structure
    required_keys = ["parameters", "critical_calculations", "scoring_weights"]
    
    if not all(key in rules for key in required_keys):
        raise HTTPException(
            status_code=400,
            detail=f"Rules must contain: {required_keys}"
        )
    
    # Save to file (in production, use database)
    rules_path = Path(__file__).parent.parent / "compliance_rules.json"
    with open(rules_path, "w") as f:
        json.dump(rules, f, indent=2)
    
    return {"message": "Rules updated successfully"}

@app.post(f"{settings.api_prefix}/meta-analysis/trend")
async def perform_trend_analysis(
    background_tasks: BackgroundTasks,
    submission_id: str
):
    """
    Perform Lake Assessment trend analysis on multiple reports
    Automatically triggered when 3+ reports from the same lake are uploaded
    """
    # Get submission metadata
    if submission_id not in meta_analysis_data:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    meta_data = meta_analysis_data[submission_id]
    analysis_ids = meta_data.get("analysis_ids", [])
    
    if len(analysis_ids) < 3:
        return {
            "success": False,
            "message": "Insufficient reports for trend analysis. Minimum 3 reports required."
        }
    
    # Collect all analyzed reports
    reports = []
    for aid in analysis_ids:
        if aid in analysis_results:
            result = analysis_results[aid]
            if result.get("status") == "complete":
                reports.append(result)
    
    if len(reports) < 3:
        return {
            "success": False,
            "message": "Not enough completed analyses for trend analysis"
        }
    
    # Perform Lake Assessment
    assessment_results = lake_assessment.perform_assessment(reports)
    
    if not assessment_results:
        return {
            "success": False,
            "message": "Unable to group reports by lake or insufficient data"
        }
    
    # Generate Lake Assessment reports
    assessment_paths = {}
    for lake_name, assessment_data in assessment_results.items():
        report_path = lake_assessment_report.generate_assessment_report(assessment_data)
        assessment_paths[lake_name] = report_path
    
    # Store results
    meta_data["assessment_complete"] = True
    meta_data["assessment_reports"] = assessment_paths
    meta_data["assessment_timestamp"] = datetime.now().isoformat()
    
    # Send notification with Lake Assessment report
    contact_info = meta_data.get("contact_info", {})
    if email_service.is_configured() and assessment_paths:
        # Send email with Lake Assessment attached
        for lake_name, report_path in assessment_paths.items():
            email_service.send_lake_assessment_notification(
                customer_name=contact_info.get("name", "Unknown"),
                customer_email=contact_info.get("email", "Unknown"),
                lake_name=lake_name,
                report_path=report_path,
                year_range=assessment_results[lake_name].get("year_range", "Unknown")
            )
    
    return {
        "success": True,
        "submission_id": submission_id,
        "lakes_analyzed": list(assessment_paths.keys()),
        "assessment_reports": assessment_paths,
        "message": f"Lake Assessment completed for {len(assessment_paths)} lake(s)"
    }

@app.get(f"{settings.api_prefix}/meta-analysis/{{submission_id}}/status")
async def get_trend_analysis_status(submission_id: str):
    """Check the status of a Lake Assessment trend analysis"""
    if submission_id not in meta_analysis_data:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    meta_data = meta_analysis_data[submission_id]
    analysis_ids = meta_data.get("analysis_ids", [])
    
    # Check status of individual analyses
    completed = 0
    in_progress = 0
    for aid in analysis_ids:
        if aid in analysis_results:
            if analysis_results[aid]["status"] == "complete":
                completed += 1
            else:
                in_progress += 1
    
    # Check if Lake Assessment was performed
    assessment_complete = meta_data.get("assessment_complete", False)
    assessment_reports = meta_data.get("assessment_reports", {})
    
    return {
        "submission_id": submission_id,
        "total_reports": len(analysis_ids),
        "completed_analyses": completed,
        "in_progress_analyses": in_progress,
        "assessment_complete": assessment_complete,
        "assessment_reports": assessment_reports,
        "can_perform_assessment": completed >= 3,
        "timestamp": meta_data.get("assessment_timestamp")
    }

@app.get(f"{settings.api_prefix}/meta-analysis/{{submission_id}}/report/{{lake_name}}")
async def download_assessment_report(submission_id: str, lake_name: str):
    """Download a Lake Assessment report"""
    if submission_id not in meta_analysis_data:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    meta_data = meta_analysis_data[submission_id]
    assessment_reports = meta_data.get("assessment_reports", {})
    
    if lake_name not in assessment_reports:
        raise HTTPException(status_code=404, detail="Assessment report not found for this lake")
    
    report_path = assessment_reports[lake_name]
    
    if not Path(report_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        report_path,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=f"{lake_name}_Lake_Assessment.docx"
    )

# Add background task to automatically trigger Lake Assessment
async def check_and_trigger_assessment(submission_id: str):
    """Background task to check and trigger Lake Assessment when reports are complete"""
    import asyncio
    
    # Wait for all reports to complete (max 5 minutes)
    max_wait = 300  # 5 minutes
    start_time = datetime.now()
    
    while (datetime.now() - start_time).total_seconds() < max_wait:
        meta_data = meta_analysis_data.get(submission_id)
        if not meta_data:
            return
        
        analysis_ids = meta_data.get("analysis_ids", [])
        all_complete = True
        reports = []
        
        for aid in analysis_ids:
            if aid in analysis_results:
                result = analysis_results[aid]
                if result["status"] != "complete":
                    all_complete = False
                    break
                reports.append(result)
        
        if all_complete and len(reports) >= 3:
            # Check if Lake Assessment should be performed
            if lake_assessment.should_perform_assessment(reports):
                logger.info(f"Automatically triggering Lake Assessment for submission {submission_id}")
                
                # Perform assessment
                assessment_results = lake_assessment.perform_assessment(reports)
                
                if assessment_results:
                    # Generate reports
                    assessment_paths = {}
                    for lake_name, assessment_data in assessment_results.items():
                        report_path = lake_assessment_report.generate_assessment_report(assessment_data)
                        assessment_paths[lake_name] = report_path
                    
                    # Store results
                    meta_data["assessment_complete"] = True
                    meta_data["assessment_reports"] = assessment_paths
                    meta_data["assessment_timestamp"] = datetime.now().isoformat()
                    meta_data["assessment_auto_triggered"] = True
                    
                    logger.info(f"Lake Assessment completed for submission {submission_id}")
            return
        
        # Wait 10 seconds before checking again
        await asyncio.sleep(10)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
