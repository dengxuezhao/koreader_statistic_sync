import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import datetime
from app.entity.book import Book
from app.utils.paginator import PaginatedBookList


# OPDS常量
ATOM_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DIR_MIME = "application/atom+xml;profile=opds-catalog;kind=navigation"
DIR_REL = "subsection"
FILE_REL = "http://opds-spec.org/acquisition"
COVER_REL = "http://opds-spec.org/cover"


class Entry:
    """OPDS条目，表示目录项或书籍"""
    
    def __init__(
        self,
        id: str,
        title: str,
        updated: str,
        author: str = "",
        summary: str = "",
        links: List[Dict[str, str]] = None
    ):
        """
        初始化OPDS条目
        
        Args:
            id: 条目ID
            title: 条目标题
            updated: 更新时间，格式为ATOM_TIME_FORMAT
            author: 作者名称
            summary: 摘要
            links: 链接列表
        """
        self.id = id
        self.title = title
        self.updated = updated
        self.author = author
        self.summary = summary
        self.links = links or []
    
    def to_element(self) -> ET.Element:
        """
        转换为ElementTree元素
        
        Returns:
            ET.Element: ElementTree元素
        """
        entry = ET.Element("entry")
        
        # 添加ID
        id_elem = ET.SubElement(entry, "id")
        id_elem.text = self.id
        
        # 添加标题
        title_elem = ET.SubElement(entry, "title")
        title_elem.text = self.title
        
        # 添加更新时间
        updated_elem = ET.SubElement(entry, "updated")
        updated_elem.text = self.updated
        
        # 添加作者（如果有）
        if self.author:
            author_elem = ET.SubElement(entry, "author")
            name_elem = ET.SubElement(author_elem, "name")
            name_elem.text = self.author
        
        # 添加摘要（如果有）
        if self.summary:
            summary_elem = ET.SubElement(entry, "summary")
            summary_elem.set("type", "text")
            summary_elem.text = self.summary
        
        # 添加链接
        for link in self.links:
            link_elem = ET.SubElement(entry, "link")
            for key, value in link.items():
                link_elem.set(key, value)
        
        return entry


class Feed:
    """OPDS Feed，表示OPDS目录"""
    
    def __init__(
        self,
        id: str,
        title: str,
        updated: str,
        links: List[Dict[str, str]] = None,
        entries: List[Entry] = None
    ):
        """
        初始化OPDS Feed
        
        Args:
            id: Feed ID
            title: Feed标题
            updated: 更新时间，格式为ATOM_TIME_FORMAT
            links: 链接列表
            entries: 条目列表
        """
        self.id = id
        self.title = title
        self.updated = updated
        self.links = links or []
        self.entries = entries or []
    
    def to_element(self) -> ET.Element:
        """
        转换为ElementTree元素
        
        Returns:
            ET.Element: ElementTree元素
        """
        feed = ET.Element("feed")
        feed.set("xmlns", "http://www.w3.org/2005/Atom")
        
        # 添加ID
        id_elem = ET.SubElement(feed, "id")
        id_elem.text = self.id
        
        # 添加标题
        title_elem = ET.SubElement(feed, "title")
        title_elem.text = self.title
        
        # 添加更新时间
        updated_elem = ET.SubElement(feed, "updated")
        updated_elem.text = self.updated
        
        # 添加链接
        for link in self.links:
            link_elem = ET.SubElement(feed, "link")
            for key, value in link.items():
                link_elem.set(key, value)
        
        # 添加条目
        for entry in self.entries:
            feed.append(entry.to_element())
        
        return feed
    
    def to_xml(self) -> str:
        """
        转换为XML字符串
        
        Returns:
            str: XML字符串
        """
        root = self.to_element()
        
        # 创建ElementTree
        tree = ET.ElementTree(root)
        
        # 转换为字符串
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += ET.tostring(root, encoding="unicode")
        
        return xml_str


def build_feed(
    id: str,
    title: str,
    href: str,
    entries: List[Entry],
    additional_links: List[Dict[str, str]] = None
) -> Feed:
    """
    构建OPDS Feed
    
    Args:
        id: Feed ID
        title: Feed标题
        href: Feed链接
        entries: 条目列表
        additional_links: 附加链接列表
        
    Returns:
        Feed: OPDS Feed
    """
    # 基本链接
    links = [
        {
            "href": "/opds/",
            "type": DIR_MIME,
            "rel": "start"
        },
        {
            "href": href,
            "type": DIR_MIME,
            "rel": "self"
        },
        {
            "href": "/opds/search/{searchTerms}/",
            "type": "application/atom+xml",
            "rel": "search"
        }
    ]
    
    # 添加附加链接
    if additional_links:
        links.extend(additional_links)
    
    # 构建Feed
    return Feed(
        id=id,
        title=title,
        updated=datetime.datetime.now().strftime(ATOM_TIME_FORMAT),
        links=links,
        entries=entries
    )


def books_to_entries(books: List[Book]) -> List[Entry]:
    """
    将书籍列表转换为OPDS条目列表
    
    Args:
        books: 书籍列表
        
    Returns:
        List[Entry]: OPDS条目列表
    """
    entries = []
    
    for book in books:
        # 创建链接
        links = [
            {
                "href": f"/opds/book/{book.id}/download",
                "type": book.mime_type(),
                "rel": FILE_REL
            }
        ]
        
        # 如果有封面，添加封面链接
        if book.cover_path:
            links.append({
                "href": f"/opds/book/{book.id}/cover",
                "type": "image/jpeg",
                "rel": COVER_REL
            })
        
        # 创建条目
        entry = Entry(
            id=book.id,
            title=book.title,
            updated=book.updated_at.strftime(ATOM_TIME_FORMAT),
            author=book.author,
            links=links
        )
        
        entries.append(entry)
    
    return entries


def form_navigation_links(base_url: str, books: PaginatedBookList) -> List[Dict[str, str]]:
    """
    构建导航链接
    
    Args:
        base_url: 基础URL
        books: 分页书籍列表
        
    Returns:
        List[Dict[str, str]]: 导航链接列表
    """
    links = [
        {
            "href": base_url,
            "type": DIR_MIME,
            "rel": "start"
        },
        {
            "href": f"{base_url}?page={books.last_page()}",
            "type": DIR_MIME,
            "rel": "last"
        }
    ]
    
    # 添加下一页链接
    if books.has_next():
        links.append({
            "href": f"{base_url}?page={books.next_page()}",
            "type": DIR_MIME,
            "rel": "next"
        })
    
    # 添加上一页链接
    if books.has_prev():
        links.append({
            "href": f"{base_url}?page={books.prev_page()}",
            "type": DIR_MIME,
            "rel": "prev"
        })
    
    return links 