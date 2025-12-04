import pdfplumber
import re
from typing import Optional

class PDFParser:
    def __init__(self):
        pass
    
    def parse(self, pdf_path: str) -> str:
        """
        解析PDF文件，提取文本内容
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        text_content = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        cleaned_text = self._clean_text(page_text)
                        text_content.append(cleaned_text)
        
        except Exception as e:
            raise Exception(f"PDF parsing failed: {str(e)}")
        
        return "\n\n".join(text_content)
    
    def _clean_text(self, text: str) -> str:
        """
        清洗文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        # 移除多余的空格和换行
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符但保留常用标点
        text = re.sub(r'[^\w\s.,;:!?@()\-/\n]', '', text)
        # 分段处理
        paragraphs = text.split('\n')
        cleaned_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 5:  # 过滤过短的段落
                cleaned_paragraphs.append(para)
        
        return '\n'.join(cleaned_paragraphs)