"""
Semantic Chunker for Vietnamese Legal Documents
Optimized for Quyết định, Quy định, Quy chế documents
"""
import re
from typing import List, Dict

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document


class LegalDocumentChunker:
    """
    Semantic chunking for Vietnamese legal documents.
    Chunks by Article (Điều) to preserve complete context and prevent
    tables/clauses from being separated.
    """
    
    def __init__(self, max_chunk_size: int = 1000):
        """
        Initialize legal document chunker
        
        Args:
            max_chunk_size: Maximum characters per chunk (default 1000)
                           Stable now because embeddings.py handles token truncation.
        """
        self.max_chunk_size = max_chunk_size
        print(f"  [+] LegalDocumentChunker: max_chunk_size = {max_chunk_size} chars")
    
    def chunk_document(self, text: str, metadata: dict = None) -> List[Document]:
        """
        Chunk document by Articles (Điều)
        """
        if metadata is None:
            metadata = {}
        
        chunks = []
        
        # === BƯỚC 1: Tìm tất cả Chương trong văn bản ===
        # Formats: ## Chương I, **Chương I**, ## CHƯƠNG I, ## **CHƯƠNG I**
        chapter_pattern = r'^(?:#{1,3}\s+)?(?:\*\*)?(?:Chương|CHƯƠNG)\s+([IVXLC]+(?:\s*[-–:.].*?)?)\s*(?:\*\*)?$'
        chapter_matches = list(re.finditer(chapter_pattern, text, re.MULTILINE | re.IGNORECASE))
        
        # Xây dựng bảng tra: vị_trí -> tên_chương
        chapter_map = []  # [(start_pos, chapter_name), ...]
        for cm in chapter_matches:
            # Lấy dòng tiếp theo (có thể là tiêu đề chương)
            chapter_num = cm.group(1).strip().rstrip('.*:–- ')
            
            # Tìm tiêu đề chương ở dòng kế tiếp
            next_line_start = cm.end()
            next_line_end = text.find('\n', next_line_start + 1)
            if next_line_end == -1:
                next_line_end = len(text)
            next_line = text[next_line_start:next_line_end].strip().strip('*#').strip()
            
            if next_line and not re.match(r'(?:Điều|Phụ lục)', next_line, re.IGNORECASE):
                chapter_name = f"Chương {chapter_num}: {next_line}"
            else:
                chapter_name = f"Chương {chapter_num}"
            
            chapter_map.append((cm.start(), chapter_name))
        
        if chapter_map:
            print(f"  [*] Found {len(chapter_map)} chapters")
            # for _, name in chapter_map:
            #     print(f"    - {name}")
        
        # === BƯỚC 2: Tìm Điều/Phụ lục/Slide markers ===
        # Match multiple formats of article/section markers (CASE-INSENSITIVE):
        # - **Điều 1.** / **ĐIỀU 1.** (bold format)
        # - ### Điều 1. (markdown heading from Gemini OCR)
        # - ## **Phụ lục 07** / **PHỤ LỤC 1** (appendix)
        # - ## Slide 15 / ## Slide 16 (presentation slides)
        # - ## **Tiêu đề** (general markdown headers)
        article_pattern = r'^(?:#{1,3}\s+)?(?:\*\*)?(?:Điều|Phụ lục|Slide)\s+(\d+)'
        matches = list(re.finditer(article_pattern, text, re.MULTILINE | re.IGNORECASE))
        
        # Nếu không tìm thấy các marker đặc biệt, thử tìm bất kỳ tiêu đề Markdown nào (## Tiêu đề)
        if not matches:
            markdown_header_pattern = r'^##\s+(.*)$'
            matches = list(re.finditer(markdown_header_pattern, text, re.MULTILINE))
        
        # Nếu vẫn không tìm thấy, thử tìm section headings: ## 1. TIÊU ĐỀ
        if not matches:
            section_pattern = r'^#{1,3}\s+(\d+)\.\s+[A-ZĐÀÁẢÃẠÈÉẺẼẸÌÍỈĨỊÒÓỎÕỌÙÚỦŨỤÝỲỶỸỴÊÔƠƯĂ]'
            matches = list(re.finditer(section_pattern, text, re.MULTILINE))
        
        if not matches:
            # No articles found, treat as simple document
            print(f"  [!] No article markers found in {metadata.get('filename', 'document')}, using fallback")
            return self._recursive_split_text(text, metadata)
        
        print(f"  [+] Found {len(matches)} articles/appendices:")
        
        # Show Phụ lục matches (priority)
        phu_luc_matches = [m for m in matches if m.group(0) and 'phụ lục' in m.group(0).lower()]
        if phu_luc_matches:
            print(f"    [P] Phụ lục found ({len(phu_luc_matches)}):")
            for m in phu_luc_matches:
                val = m.group(1) if m.lastindex else m.group(0)
                print(f"      - Phụ lục {val}")
        
        # Show first 10 Điều (ASCII only numbers)
        dieu_matches = [m for m in matches if 'điều' in m.group(0).lower()][:10]
        # for match in dieu_matches:
        #     print(f"    - Dieu {match.group(1)}")
        
        # === Helper: Tìm Chương cho vị trí cụ thể ===
        def get_chapter_for_position(pos):
            """Trả về tên Chương chứa vị trí pos"""
            current_chapter = None
            for ch_pos, ch_name in chapter_map:
                if ch_pos <= pos:
                    current_chapter = ch_name
                else:
                    break
            return current_chapter
        
        # Handle document header (before first Điều)
        first_article_start = matches[0].start()
        if first_article_start > 0:
            header_text = text[:first_article_start]
            if header_text.strip():
                header_chunks = self._chunk_header(header_text, metadata)
                chunks.extend(header_chunks)
        
        # === BƯỚC 3: Chunk từng Điều + ghi metadata Chương ===
        for i, match in enumerate(matches):
            article_num = match.group(1) if match.lastindex else getattr(match, "group", lambda x: "1")(0)
            if not article_num: # fallback if empty capture group
                article_num = str(i + 1)
            article_start = match.start()
            
            # Find where this article ends (start of next article or end of text)
            if i + 1 < len(matches):
                article_end = matches[i + 1].start()
            else:
                article_end = len(text)
            
            article_text = text[article_start:article_end].strip()
            
            # Xác định Chương cho Điều này
            chapter = get_chapter_for_position(article_start)
            
            # Build metadata cho chunk
            chunk_meta = {
                **metadata,
                'chunk_type': 'article',
                'article': article_num,
                'complete': True
            }
            if chapter:
                chunk_meta['chapter'] = chapter
            
            # Check if article fits in one chunk
            if len(article_text) <= self.max_chunk_size:
                chunks.append(Document(
                    page_content=article_text,
                    metadata=chunk_meta
                ))
            else:
                # Split long article but keep header
                sub_chunks = self._split_long_article(article_text, article_num, metadata, chapter)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _chunk_header(self, header_text: str, base_metadata: dict) -> List[Document]:
        """Handle document header section"""
        # For header, we often have titles, decisions info. 
        # We split it into reasonable pieces.
        return self._recursive_split_text(header_text, {**base_metadata, 'chunk_type': 'header'})

    def _split_long_article(self, article_text: str, article_num: str, base_metadata: dict, chapter: str = None) -> List[Document]:
        """Split long article into sub-chunks by numbered clauses (khoản), preserving article header"""
        lines = article_text.split('\n')
        header = lines[0]   # e.g. "**Điều 8. Tổ chức giảng dạy và học tập**"
        content_lines = lines[1:]
        
        max_content_size = self.max_chunk_size - len(header) - 10
        
        # === Tìm ranh giới khoản: dòng bắt đầu bằng "số." hoặc "số. " ===
        # Pattern: "1.", "2.", "6. Trách..." ở đầu dòng (sau strip indent nhẹ)
        clause_pattern = re.compile(r'^(\d+)\.\s+\S')
        
        # Tìm vị trí bắt đầu của từng khoản trong content_lines
        clause_starts = []  # [(line_index, clause_num), ...]
        for i, line in enumerate(content_lines):
            stripped = line.strip()
            m = clause_pattern.match(stripped)
            if m:
                clause_num = int(m.group(1))
                # Chỉ nhận khoản số hợp lệ (1-99, theo thứ tự tăng dần)
                if not clause_starts or clause_num > clause_starts[-1][1]:
                    clause_starts.append((i, clause_num))
        
        chunks = []
        
        if len(clause_starts) >= 2:
            # Tách theo khoản: nhóm các khoản sao cho mỗi chunk <= max_content_size
            current_group_start = 0   # line index
            current_size = 0
            
            for ci, (line_idx, clause_num) in enumerate(clause_starts):
                # Xác định end của khoản này
                if ci + 1 < len(clause_starts):
                    next_start = clause_starts[ci + 1][0]
                else:
                    next_start = len(content_lines)
                
                clause_text = '\n'.join(content_lines[line_idx:next_start])
                clause_size = len(clause_text)
                
                # Nếu thêm khoản này sẽ vượt quá max → flush chunk hiện tại trước
                if current_size + clause_size > max_content_size and current_size > 0:
                    group_text = '\n'.join(content_lines[current_group_start:line_idx])
                    chunks.append(group_text)
                    current_group_start = line_idx
                    current_size = clause_size
                else:
                    current_size += clause_size
            
            # Flush nhóm cuối
            remaining = '\n'.join(content_lines[current_group_start:])
            if remaining.strip():
                chunks.append(remaining)
        
        # Fallback: không tìm thấy khoản có thứ tự → tách theo paragraph
        if not chunks:
            sub_docs = self._recursive_split_text(
                '\n'.join(content_lines), base_metadata, max_size=max_content_size
            )
            chunks = [doc.page_content for doc in sub_docs]
        
        # Tạo Document cho mỗi chunk, giữ header Điều
        result = []
        for i, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
            chunk_meta = {
                **base_metadata,
                'chunk_type': 'article_part',
                'article': article_num,
                'part': i + 1,
                'complete': False
            }
            if chapter:
                chunk_meta['chapter'] = chapter
            result.append(Document(
                page_content=f"{header}\n(Phần {i+1})\n{chunk_text}",
                metadata=chunk_meta
            ))
        return result

    def _recursive_split_text(self, text: str, base_metadata: dict, max_size: int = None) -> List[Document]:
        """Recursively split text into chunks that fit max_size"""
        if max_size is None:
            max_size = self.max_chunk_size
            
        if len(text) <= max_size:
            return [Document(page_content=text, metadata=base_metadata)]
        
        # Try to split at logical points: paragraphs, sentences, spaces
        separators = ["\n\n", "\n", ". ", " ", ""]
        final_chunks = []
        
        current_text = text
        while len(current_text) > max_size:
            split_idx = -1
            for sep in separators:
                if not sep: # last resort: hard cut
                    split_idx = max_size
                    break
                
                # Find the last occurrence of sep within the first max_size chars
                idx = current_text.rfind(sep, 0, max_size)
                if idx != -1:
                    split_idx = idx + len(sep)
                    break
            
            chunk = current_text[:split_idx].strip()
            if chunk:
                final_chunks.append(Document(page_content=chunk, metadata=base_metadata))
            current_text = current_text[split_idx:].strip()
            
        if current_text:
            final_chunks.append(Document(page_content=current_text, metadata=base_metadata))
            
        return final_chunks
