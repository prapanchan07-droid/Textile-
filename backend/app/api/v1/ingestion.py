from typing import Optional, List
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import StandardResponse
from app.services.ingestion.ingestion_service import IngestionService, IngestionJobManager
from app.services.template.template_builder import build_template_xlsx

router = APIRouter(prefix="/ingestion", tags=["Report Data Ingestion"])

@router.get("/template")
def download_data_template(sample: bool = Query(False, description="Pre-fill the template with 7 days of sample data")):
    """Download the Excel data template. Fill it in and upload it to update every dashboard page."""
    filename = "factory_data_sample.xlsx" if sample else "factory_data_template.xlsx"
    return Response(
        content=build_template_xlsx(with_sample=sample),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.post("/upload-job",response_model=StandardResponse[dict])
async def upload_multiple_reports_job(
    files: List[UploadFile] = File(...),
    report_type_override: Optional[str] = Form(None),
    date_override: Optional[str] = Form(None),
    force_replace: bool = Form(False),
):
    try:
        files_payload = []
        for file in files:
            content = await file.read()
            files_payload.append((content, file.filename or "uploaded_report"))

        job_id = IngestionJobManager.create_job(total_files=len(files_payload))
        IngestionJobManager.run_job_in_background(
            job_id=job_id,
            files_payload=files_payload,
            report_type_override=report_type_override,
            date_override=date_override,
            force_replace=force_replace
        )

        return StandardResponse(
            success=True,
            message="Ingestion job initiated.",
            data={"job_id": job_id, "total_files": len(files_payload)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate ingestion job: {str(e)}"
        )

@router.get("/job/{job_id}", response_model=StandardResponse[dict])
def get_job_status(job_id: str):
    job = IngestionJobManager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{job_id}' not found."
        )
    return StandardResponse(success=True, data=job)

@router.post("/upload", response_model=StandardResponse[dict])
async def upload_report_file(
    file: UploadFile = File(...),
    report_type_override: Optional[str] = Form(None),
    date_override: Optional[str] = Form(None),
    force_replace: bool = Form(False),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        res = IngestionService.process_upload(
            db=db,
            file_bytes=content,
            filename=file.filename or "uploaded_report",
            report_type_override=report_type_override,
            date_override=date_override,
            force_replace=force_replace
        )
        if res.get("status") == "DUPLICATE":
            return StandardResponse(
                success=False,
                message=res["message"],
                data=res
            )
        return StandardResponse(
            success=True,
            message="Report ingested successfully.",
            data=res
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report processing failed: {str(e)}"
        )

@router.get("/history", response_model=StandardResponse[list])
def get_ingestion_history(db: Session = Depends(get_db)):
    history = IngestionService.get_upload_history(db)
    return StandardResponse(success=True, data=history)
