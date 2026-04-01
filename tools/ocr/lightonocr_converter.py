"""
LightOnOCR Converter - OCR for Scanned PDFs

Uses LightOnOCR-2-1B model to extract text from scanned PDFs.
Model runs locally and supports GPU acceleration.
"""

from pathlib import Path
from typing import Union, List
import logging
from PIL import Image

try:
    from transformers import AutoProcessor, AutoModelForVision2Seq
    import torch
except ImportError:
    raise ImportError(
        "Transformers and torch are required. Install with:\n"
        "pip install transformers>=4.30.0 torch>=2.0.0"
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

# Model configuration
MODEL_NAME = "lightonai/LightOnOCR-2-1B"


class LightOnOCRConverter:
    """
    OCR converter using LightOnOCR-2-1B model.
    Supports GPU acceleration if available.
    """
    
    def __init__(self, device: str = None):
        """
        Initialize LightOnOCR converter.
        
        Args:
            device: Device to use ('cuda' or 'cpu'). Auto-detects if None.
        """
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"🚀 Initializing LightOnOCR-2-1B on {self.device.upper()}...")
        
        if self.device == "cpu":
            logger.warning("⚠️  Running on CPU - OCR will be slow. Consider using GPU for faster processing.")
        
        # Load model and processor
        try:
            self.processor = AutoProcessor.from_pretrained(MODEL_NAME)
            self.model = AutoModelForVision2Seq.from_pretrained(MODEL_NAME)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info("✅ LightOnOCR model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load LightOnOCR model: {e}")
            raise Exception(f"Model loading failed: {e}") from e
    
    def ocr_image(self, image: Image.Image) -> str:
        """
        Perform OCR on a single image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text as string
        """
        try:
            # Process image
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate text with proper parameters
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=2048,
                    do_sample=False,
                    num_beams=1
                )
            
            # Decode output - handle case where output may be empty
            if generated_ids is not None and len(generated_ids) > 0:
                decoded = self.processor.batch_decode(
                    generated_ids, 
                    skip_special_tokens=True
                )
                if decoded and len(decoded) > 0:
                    text = decoded[0]
                    return text.strip()
            
            logger.warning("No text extracted from image")
            return ""
            
        except Exception as e:
            logger.error(f"OCR failed for image: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def convert_pdf(self, file_path: Union[str, Path], dpi: int = 300) -> Path:
        """
        Convert scanned PDF to Markdown using OCR.
        
        Args:
            file_path: Path to the PDF file
            dpi: DPI for PDF to image conversion (higher = better quality but slower)
            
        Returns:
            Path to the generated .md file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"Expected PDF file, got: {file_path.suffix}")
        
        logger.info(f"📄 Converting scanned PDF: {file_path.name}")
        logger.info(f"   DPI: {dpi}, Device: {self.device.upper()}")
        
        try:
            # Convert PDF to images
            logger.info("🖼️  Converting PDF pages to images...")
            images = convert_from_path(str(file_path), dpi=dpi)
            logger.info(f"   Found {len(images)} pages")
            
            # Process each page
            markdown_lines = [f"# {file_path.stem}\n"]
            markdown_lines.append(f"_Extracted from scanned PDF using LightOnOCR-2-1B_\n")
            
            for i, image in enumerate(images, 1):
                logger.info(f"🔍 Processing page {i}/{len(images)}...")
                
                # Perform OCR
                text = self.ocr_image(image)
                
                # Add to markdown
                markdown_lines.append(f"\n## Page {i}\n")
                markdown_lines.append(text)
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
            raise Exception(f"LightOnOCR conversion failed: {e}") from e


# Global converter instance (lazy loading)
_converter_instance = None


def get_converter() -> LightOnOCRConverter:
    """
    Get or create global converter instance (singleton pattern).
    Avoids reloading the model multiple times.
    """
    global _converter_instance
    
    if _converter_instance is None:
        _converter_instance = LightOnOCRConverter()
    
    return _converter_instance


def convert_pdf_with_lightonocr(file_path: Union[str, Path], dpi: int = 300) -> Path:
    """
    Convenience function to convert PDF using LightOnOCR.
    Uses singleton pattern to avoid reloading model.
    
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
        print("Usage: python lightonocr_converter.py <pdf_file>")
        print("Example: python lightonocr_converter.py scanned.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        output_file = convert_pdf_with_lightonocr(input_file)
        print(f"\n✅ Success! Markdown file created: {output_file}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
