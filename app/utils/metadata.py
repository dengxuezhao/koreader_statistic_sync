import os
import io
import logging
from typing import Dict, Any, Optional
from PIL import Image
from io import BytesIO

# 导入支持不同电子书格式的库
import ebooklib
from ebooklib import epub
import PyPDF2
import zipfile
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class BookMetadata:
    """书籍元数据类，存储从电子书中提取的元数据"""
    
    def __init__(self):
        self.title = ""
        self.author = ""
        self.publisher = ""
        self.isbn = ""
        self.format = ""
        self.cover = None  # 封面图像的二进制数据
    
    def __str__(self):
        return f"BookMetadata(title='{self.title}', author='{self.author}', publisher='{self.publisher}', isbn='{self.isbn}', format='{self.format}')"


def extract_book_metadata(file_path: str) -> BookMetadata:
    """
    从电子书文件中提取元数据
    
    Args:
        file_path: 电子书文件的路径
        
    Returns:
        BookMetadata: 提取的元数据
    """
    metadata = BookMetadata()
    
    # 根据文件扩展名确定格式并提取元数据
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".epub":
            metadata = extract_epub_metadata(file_path)
        elif ext == ".pdf":
            metadata = extract_pdf_metadata(file_path)
        elif ext == ".mobi":
            metadata = extract_mobi_metadata(file_path)
        elif ext == ".fb2":
            metadata = extract_fb2_metadata(file_path)
        else:
            logger.warning(f"Unsupported book format: {ext}")
            # 保存格式信息，即使无法提取其他元数据
            metadata.format = ext.lstrip(".")
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
    
    # 如果标题为空，使用文件名作为标题
    if not metadata.title:
        metadata.title = os.path.basename(file_path)
    
    return metadata


def extract_epub_metadata(file_path: str) -> BookMetadata:
    """从EPUB文件中提取元数据"""
    metadata = BookMetadata()
    metadata.format = "epub"
    
    try:
        book = epub.read_epub(file_path)
        
        # 提取标题和作者
        if book.get_metadata('DC', 'title'):
            metadata.title = book.get_metadata('DC', 'title')[0][0]
        
        if book.get_metadata('DC', 'creator'):
            metadata.author = book.get_metadata('DC', 'creator')[0][0]
        
        # 提取出版商
        if book.get_metadata('DC', 'publisher'):
            metadata.publisher = book.get_metadata('DC', 'publisher')[0][0]
        
        # 提取ISBN
        for identifier in book.get_metadata('DC', 'identifier'):
            if 'isbn' in str(identifier).lower():
                metadata.isbn = identifier[0]
                break
        
        # 提取封面
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if 'cover' in item.id.lower() or 'cover' in item.file_name.lower():
                metadata.cover = item.content
                break
        
    except Exception as e:
        logger.error(f"Error extracting EPUB metadata: {str(e)}")
    
    return metadata


def extract_pdf_metadata(file_path: str) -> BookMetadata:
    """从PDF文件中提取元数据"""
    metadata = BookMetadata()
    metadata.format = "pdf"
    
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            info = reader.metadata
            
            if info:
                if info.get('/Title'):
                    metadata.title = info.get('/Title')
                
                if info.get('/Author'):
                    metadata.author = info.get('/Author')
                
                if info.get('/Publisher'):
                    metadata.publisher = info.get('/Publisher')
                
                # PDF文件通常没有存储封面图像的标准方式
                # 一种方法是使用第一页作为封面
                # 但这需要额外的PDF渲染库，如Pillow或MuPDF
    
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {str(e)}")
    
    return metadata


def extract_mobi_metadata(file_path: str) -> BookMetadata:
    """从MOBI文件中提取元数据"""
    metadata = BookMetadata()
    metadata.format = "mobi"
    
    # MOBI格式较复杂，通常需要专门的库如kindleunpack
    # 这里提供一个简单的实现，实际应用中可能需要更复杂的处理
    try:
        # 尝试从文件名中提取信息
        base_name = os.path.basename(file_path)
        parts = base_name.split(' - ')
        
        if len(parts) >= 2:
            metadata.title = parts[0].strip()
            # 移除扩展名
            author_part = parts[1].replace('.mobi', '').strip()
            metadata.author = author_part
    
    except Exception as e:
        logger.error(f"Error extracting MOBI metadata: {str(e)}")
    
    return metadata


def extract_fb2_metadata(file_path: str) -> BookMetadata:
    """从FB2文件中提取元数据"""
    metadata = BookMetadata()
    metadata.format = "fb2"
    
    try:
        # FB2是XML格式的文件
        # 先检查是否是ZIP压缩的FB2
        try:
            with zipfile.ZipFile(file_path) as z:
                # 找到.fb2文件
                fb2_files = [f for f in z.namelist() if f.endswith('.fb2')]
                if fb2_files:
                    with z.open(fb2_files[0]) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                else:
                    logger.warning(f"No FB2 file found in ZIP: {file_path}")
                    return metadata
        except zipfile.BadZipFile:
            # 不是ZIP文件，直接解析
            tree = ET.parse(file_path)
            root = tree.getroot()
        
        # 提取元数据
        ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
        
        # 提取标题
        title_elem = root.find('.//fb:book-title', ns)
        if title_elem is not None and title_elem.text:
            metadata.title = title_elem.text
        
        # 提取作者
        author_elem = root.find('.//fb:author', ns)
        if author_elem is not None:
            first_name = author_elem.find('./fb:first-name', ns)
            last_name = author_elem.find('./fb:last-name', ns)
            
            author_parts = []
            if first_name is not None and first_name.text:
                author_parts.append(first_name.text)
            if last_name is not None and last_name.text:
                author_parts.append(last_name.text)
            
            metadata.author = ' '.join(author_parts)
        
        # 提取出版商
        publisher_elem = root.find('.//fb:publisher', ns)
        if publisher_elem is not None and publisher_elem.text:
            metadata.publisher = publisher_elem.text
        
        # 提取ISBN
        isbn_elem = root.find('.//fb:isbn', ns)
        if isbn_elem is not None and isbn_elem.text:
            metadata.isbn = isbn_elem.text
        
        # 提取封面
        binary_elems = root.findall('.//fb:binary', ns)
        for binary in binary_elems:
            if binary.get('content-type', '').startswith('image/'):
                # 检查是否是封面
                if binary.get('id', '').lower().startswith('cover'):
                    try:
                        image_data = binary.text
                        if image_data:
                            import base64
                            metadata.cover = base64.b64decode(image_data)
                            break
                    except Exception as e:
                        logger.error(f"Error decoding cover image: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error extracting FB2 metadata: {str(e)}")
    
    return metadata


def resize_cover(cover_data: bytes, max_size: int = 800) -> bytes:
    """
    调整封面图像大小
    
    Args:
        cover_data: 封面图像的二进制数据
        max_size: 最大尺寸（宽度或高度）
        
    Returns:
        bytes: 调整大小后的图像二进制数据
    """
    try:
        with Image.open(BytesIO(cover_data)) as img:
            # 计算新尺寸
            width, height = img.size
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                # 调整大小
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # 保存为JPEG
            output = BytesIO()
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output, format='JPEG', quality=85)
            return output.getvalue()
    
    except Exception as e:
        logger.error(f"Error resizing cover: {str(e)}")
        return cover_data  # 如果调整大小失败，返回原始数据 