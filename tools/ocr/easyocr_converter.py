"""
Enhanced EasyOCR Converter with Image Preprocessing

Uses EasyOCR with advanced image preprocessing to improve OCR accuracy.
Preprocessing includes: denoising, contrast enhancement, binarization, and deskewing.
"""

from pathlib import Path
from typing import Union
import logging
import numpy as np
import re  # For post-processing regex patterns

try:
    import easyocr
except ImportError:
    raise ImportError(
        "EasyOCR is required. Install with:\n"
        "pip install easyocr>=1.7.0"
    )

try:
    import cv2
except ImportError:
    raise ImportError(
        "OpenCV is required for image preprocessing. Install with:\n"
        "pip install opencv-python>=4.5.0"
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


class EnhancedEasyOCRConverter:
    """
    Enhanced OCR converter using EasyOCR with image preprocessing.
    Supports Vietnamese and multiple languages with improved accuracy.
    """
    
    def __init__(self, langs=['vi', 'en'], gpu=False):
        """
        Initialize Enhanced EasyOCR converter.
        
        Args:
            langs: List of language codes (default: ['vi', 'en'])
            gpu: Whether to use GPU acceleration
        """
        logger.info(f"🚀 Initializing Enhanced EasyOCR (langs={langs}, GPU={gpu})...")
        
        try:
            # Initialize EasyOCR Reader
            self.reader = easyocr.Reader(langs, gpu=gpu)
            
            logger.info("✅ Enhanced EasyOCR initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize EasyOCR: {e}")
            raise Exception(f"EasyOCR initialization failed: {e}") from e
    
    def preprocess_image(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Apply image preprocessing to improve OCR accuracy.
        
        Preprocessing steps:
        1. Convert to grayscale
        2. Denoise
        3. Increase contrast (CLAHE)
        4. Binarization (adaptive thresholding)
        5. Deskew (optional)
        
        Args:
            image_path: Path to image file
            
        Returns:
            Preprocessed image as numpy array
        """
        # Read image
        img = cv2.imread(str(image_path))
        
        if img is None:
            raise ValueError(f"Failed to read image: {image_path}")
        
        # 1. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # 3. Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)
        
        # 4. Adaptive thresholding for binarization
        binary = cv2.adaptiveThreshold(
            contrast,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # 5. Morphological operations to remove noise and connect broken characters
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return morph
    
    def ocr_image(self, image_path: Union[str, Path], use_preprocessing: bool = True) -> str:
        """
        Perform OCR on a single image with optional preprocessing.
        
        Args:
            image_path: Path to image file
            use_preprocessing: Whether to apply image preprocessing
            
        Returns:
            Extracted text as string
        """
        try:
            if use_preprocessing:
                # Preprocess image
                processed_img = self.preprocess_image(image_path)
                
                # Save preprocessed image temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    cv2.imwrite(tmp.name, processed_img)
                    temp_path = tmp.name
                
                # Run OCR on preprocessed image
                result = self.reader.readtext(temp_path)
                
                # Clean up temp file
                Path(temp_path).unlink()
            else:
                # Run OCR directly without preprocessing
                result = self.reader.readtext(str(image_path))
            
            # Extract text from result
            # EasyOCR returns [(bbox, text, confidence), ...]
            texts = [detection[1] for detection in result]
            
            return '\n'.join(texts)
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    
    def post_process_legal_markdown(self, text: str) -> str:
        """
        Post-process OCR output to format it as proper legal document markdown.
        
        Converts OCR patterns like:
        - "Điều 1:" or "Điều.2." → "**Điều 1.**"
        - "## Trang 1" → Keep as is (page headers)
        
        Args:
            text: Raw OCR markdown output
            
        Returns:
            Formatted legal document markdown
        """
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Pattern 1: "Điều X:" or "Điều.X." or "Điều X." at start of line
            # Convert to: "**Điều X.**"
            dieu_pattern = r'^(Điều|Đỉều|Điêù)[:\.]?\s*(\d+)[:\.]?\s*(.*)$'
            match = re.match(dieu_pattern, line, re.IGNORECASE)
            if match:
                article_type = "Điều"  # Normalize
                article_num = match.group(2)
                rest = match.group(3)
                line = f"**{article_type} {article_num}.** {rest}".strip()
            
            # Pattern 2: "Phụ lục X" or "Phụ lục 07 –" at start of line
            # Convert to: "## **Phụ lục X.**" (or keep existing content after)
            phu_luc_pattern = r'^(?:##\s+)?(Phụ\s*lục|Phụ\s*Iục)[:\.]?\s*(\d+)\s*(.*)$'
            match = re.match(phu_luc_pattern, line, re.IGNORECASE)
            if match:
                appendix_num = match.group(2)
                rest = match.group(3).strip()
                if rest:
                    line = f"## **Phụ lục {appendix_num}.** {rest}"
                else:
                    line = f"## **Phụ lục {appendix_num}.**"
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def convert_pdf(self, file_path: Union[str, Path], dpi: int = 300, use_preprocessing: bool = True) -> Path:
        """
        Convert scanned PDF to Markdown using OCR with preprocessing.
        
        Args:
            file_path: Path to the PDF file
            dpi: DPI for PDF to image conversion (default: 300)
            use_preprocessing: Whether to apply image preprocessing
            
        Returns:
            Path to the generated .md file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"Expected PDF file, got: {file_path.suffix}")
        
        preproc_status = "with preprocessing" if use_preprocessing else "without preprocessing"
        logger.info(f"📄 Converting scanned PDF: {file_path.name}")
        logger.info(f"   DPI: {dpi}, Preprocessing: {use_preprocessing}")
        
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
                markdown_lines.append(f"_Extracted from scanned PDF using Enhanced EasyOCR {preproc_status}_\n")
                
                for i, image in enumerate(images, 1):
                    logger.info(f"🔍 Processing page {i}/{len(images)}...")
                    
                    # Save image temporarily
                    img_path = temp_path / f"page_{i}.png"
                    image.save(img_path, "PNG")
                    
                    # Perform OCR with preprocessing
                    text = self.ocr_image(img_path, use_preprocessing=use_preprocessing)
                    
                    # Add to markdown
                    markdown_lines.append(f"\n## Trang {i}\n")
                    if text:
                        markdown_lines.append(text)
                    else:
                        markdown_lines.append("_(Không trích xuất được text)_")
                    markdown_lines.append("\n---\n")
            
            # Combine results
            markdown_content = "\n".join(markdown_lines)
            
            # Post-process to format legal document structure
            logger.info("🔧 Post-processing markdown format...")
            markdown_content = self.post_process_legal_markdown(markdown_content)
            
            # Save to file
            md_path = file_path.with_suffix('.md')
            md_path.write_text(markdown_content, encoding='utf-8')
            
            logger.info(f"✅ OCR conversion successful: {md_path.name}")
            logger.info(f"   Output size: {len(markdown_content)} characters")
            
            return md_path
            
        except Exception as e:
            logger.error(f"❌ OCR conversion failed: {e}")
            raise Exception(f"Enhanced EasyOCR conversion failed: {e}") from e


# Global converter instance (lazy loading)
_converter_instance = None


def get_converter() -> EnhancedEasyOCRConverter:
    """
    Get or create global converter instance (singleton pattern).
    Avoids reinitializing EasyOCR multiple times.
    """
    global _converter_instance
    
    if _converter_instance is None:
        _converter_instance = EnhancedEasyOCRConverter()
    
    return _converter_instance


def convert_pdf_with_easyocr(file_path: Union[str, Path], dpi: int = 300, use_preprocessing: bool = True) -> Path:
    """
    Convenience function to convert PDF using Enhanced EasyOCR.
    Uses singleton pattern to avoid reinitializing.
    
    Args:
        file_path: Path to the PDF file
        dpi: DPI for conversion (default: 300)
        use_preprocessing: Whether to apply image preprocessing (default: True)
        
    Returns:
        Path to the generated .md file
    """
    converter = get_converter()
    return converter.convert_pdf(file_path, dpi=dpi, use_preprocessing=use_preprocessing)


if __name__ == "__main__":
    # Test conversion
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python easyocr_converter.py <pdf_file> [--no-preprocessing]")
        print("Example: python easyocr_converter.py scanned.pdf")
        print("         python easyocr_converter.py scanned.pdf --no-preprocessing")
        sys.exit(1)
    
    input_file = sys.argv[1]
    use_preproc = "--no-preprocessing" not in sys.argv
    
    try:
        output_file = convert_pdf_with_easyocr(input_file, use_preprocessing=use_preproc)
        print(f"\n✅ Success! Markdown file created: {output_file}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
