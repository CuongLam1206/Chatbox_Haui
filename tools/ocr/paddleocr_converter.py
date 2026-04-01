"""
PaddleOCR Converter - OCR for Scanned PDFs

Uses PaddleOCR engine to extract text from scanned PDFs.
Supports Vietnamese language and runs locally without GPU requirement.
"""

from pathlib import Path
from typing import Union
import logging

try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError(
        "PaddleOCR is required. Install with:\n"
        "pip install paddleocr>=2.7.0"
    )

try:
    from pdf2image import convert_from_path
except ImportError:
    raise ImportError(
        "pdf2image is required. Install with: pip install pdf2image>=1.16.0\n"
        "Note: Also requires poppler-utils on Linux or poppler on Windows"
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaddleOCRConverter:
    """
    OCR converter using PaddleOCR engine.
    Supports Vietnamese and works well on CPU.
    """
    
    def __init__(self, use_gpu: bool = False, lang: str = 'vi'):
        """
        Initialize PaddleOCR converter.
        
        Args:
            use_gpu: Whether to use GPU acceleration
            lang: Language code ('vi' for Vietnamese, 'en' for English)
        """
        logger.info(f"🚀 Initializing PaddleOCR (lang={lang}, GPU={use_gpu})...")
        
        try:
            # Initialize PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=True,  # Enable text angle classification
                lang=lang,
                use_gpu=use_gpu,
                show_log=False  # Suppress verbose logs
            )
            
            logger.info("✅ PaddleOCR initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize PaddleOCR: {e}")
            raise Exception(f"PaddleOCR initialization failed: {e}") from e
    
    def ocr_image(self, image_path: Union[str, Path]) -> str:
        """
        Perform OCR on a single image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text as string
        """
        try:
            # Run OCR
            result = self.ocr.ocr(str(image_path), cls=True)
            
            # Extract text from result
            # PaddleOCR returns: [[[bbox], (text, confidence)], ...]
            if result and result[0]:
                texts = []
                for line in result[0]:
                    if line[1]:  # (text, confidence)
                        text = line[1][0]
                        texts.append(text)
                
                return '\n'.join(texts)
            
            return ""
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def convert_pdf(self, file_path: Union[str, Path], dpi: int = 300) -> Path:
        """
        Convert scanned PDF to Markdown using OCR.
        
        Args:
            file_path: Path to the PDF file
            dpi: DPI for PDF to image conversion (default: 300)
            
        Returns:
            Path to the generated .md file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"Expected PDF file, got: {file_path.suffix}")
        
        logger.info(f"📄 Converting scanned PDF: {file_path.name}")
        logger.info(f"   DPI: {dpi}")
        
        try:
            # Convert PDF to images
            logger.info("🖼️  Converting PDF pages to images...")
            images = convert_from_path(str(file_path), dpi=dpi)
            logger.info(f"   Found {len(images)} pages")
            
            # Create temp directory for images
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Process each page
                markdown_lines = [f"# {file_path.stem}\n"]
                markdown_lines.append(f"_Extracted from scanned PDF using PaddleOCR_\n")
                
                for i, image in enumerate(images, 1):
                    logger.info(f"🔍 Processing page {i}/{len(images)}...")
                    
                    # Save image temporarily
                    img_path = temp_path / f"page_{i}.png"
                    image.save(img_path, "PNG")
                    
                    # Perform OCR
                    text = self.ocr_image(img_path)
                    
                    # Add to markdown
                    markdown_lines.append(f"\n## Trang {i}\n")
                    if text:
                        markdown_lines.append(text)
                    else:
                        markdown_lines.append("_(Không trích xuất được text)_")
                    markdown_lines.append("\n---\n")
            
            # Combine results
            markdown_content = "\n".join(markdown_lines)
            
            # Save to file
            md_path = file_path.with_suffix('.md')
            md_path.write_text(markdown_content, encoding='utf-8')
            
            logger.info(f"✅ OCR conversion successful: {md_path.name}")
            logger.info(f"   Output size: {len(markdown_content)} characters")
            
            return md_path
            
        except Exception as e:
            logger.error(f"❌ OCR conversion failed: {e}")
            raise Exception(f"PaddleOCR conversion failed: {e}") from e


# Global converter instance (lazy loading)
_converter_instance = None


def get_converter() -> PaddleOCRConverter:
    """
    Get or create global converter instance (singleton pattern).
    Avoids reinitializing PaddleOCR multiple times.
    """
    global _converter_instance
    
    if _converter_instance is None:
        _converter_instance = PaddleOCRConverter()
    
    return _converter_instance


def convert_pdf_with_paddleocr(file_path: Union[str, Path], dpi: int = 300) -> Path:
    """
    Convenience function to convert PDF using PaddleOCR.
    Uses singleton pattern to avoid reinitializing.
    
    Args:
        file_path: Path to the PDF file
        dpi: DPI for conversion (default: 300)
        
    Returns:
        Path to the generated .md file
    """
    converter = get_converter()
    return converter.convert_pdf(file_path, dpi=dpi)


if __name__ == "__main__":
    # Test conversion
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python paddleocr_converter.py <pdf_file>")
        print("Example: python paddleocr_converter.py scanned.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        output_file = convert_pdf_with_paddleocr(input_file)
        print(f"\n✅ Success! Markdown file created: {output_file}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
