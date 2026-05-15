from fastapi import File, HTTPException, UploadFile
import os
from loguru import logger
from docling.document_converter import DocumentConverter
import tempfile
from fastapi.responses import FileResponse
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser

logger.info("Initializing Extraction Module (Docling)...")
try:
    converter = DocumentConverter()

except Exception as e:
    logger.error(f"Failed to load models: {e}")
    raise


def run_conversion(temp_path: str):
    """Sync wrapper for Docling to be run in a thread pool."""
    result = converter.convert(temp_path)
    return result.document.export_to_markdown()


async def send_message_marker(pdf_file: UploadFile = File(...)):
    try:
        if not pdf_file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        logger.info(f"Processing uploaded file: {pdf_file.filename}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            content = await pdf_file.read()
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name

            config = {"output_format": "json", "force_ocr": True}
            config_parser = ConfigParser(config)

            converter = PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=create_model_dict(),
            )
            rendered = converter(temp_pdf_path)
            print(rendered)
            text, _, images = text_from_rendered(rendered)
            print(text)

            logger.info(
                f"PDF converted to sentences successfully: {len(text)} sentences extracted"
            )

            os.unlink(temp_pdf_path)

            return {"text": text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def extract_text(pdf_file: UploadFile = File(...)):
    # TODO: Add support for other file types in the future, but for now only PDF is supported.
    """Only PDF files are supported."""
    try:
        if not pdf_file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        logger.info(f"Processing uploaded file: {pdf_file.filename}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            content = await pdf_file.read()
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name

        converter = DocumentConverter()
        doc = converter.convert(temp_pdf_path).document

        text = doc.export_to_markdown()
        logger.info("PDF converted to markdown successfully with Docling")
        logger.info(
            f"PDF converted to sentences successfully: {len(text)} sentences extracted"
        )

        os.unlink(temp_pdf_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as temp_md:
            temp_md.write(text.encode("utf-8"))
            temp_md_path = temp_md.name

        logger.info(f"Markdown file created at: {temp_md_path}")
        return FileResponse(
            path=temp_md_path, media_type="text/markdown", filename="extracted_text.md"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
