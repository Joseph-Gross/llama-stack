# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from pydantic import BaseModel, Field

from llama_stack.apis.common.content_types import URL, InterleavedContent
from llama_stack.providers.utils.telemetry.trace_protocol import trace_protocol
from llama_stack.schema_utils import json_schema_type, webmethod


class DocumentStatus(Enum):
    """Status of a document in the knowledge base.
    
    :cvar PENDING: Document is pending processing
    :cvar PROCESSING: Document is being processed
    :cvar INDEXED: Document has been indexed
    :cvar FAILED: Document processing failed
    """
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentType(Enum):
    """Types of documents supported by the knowledge connector.
    
    :cvar PDF: PDF document
    :cvar DOCX: Microsoft Word document
    :cvar TXT: Plain text document
    :cvar HTML: HTML document
    :cvar CSV: CSV data file
    :cvar JSON: JSON data file
    :cvar IMAGE: Image file
    """
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    IMAGE = "image"


class DataSourceType(Enum):
    """Types of enterprise data sources.
    
    :cvar SHAREPOINT: Microsoft SharePoint
    :cvar ONEDRIVE: Microsoft OneDrive
    :cvar GDRIVE: Google Drive
    :cvar S3: Amazon S3
    :cvar DATABASE: SQL/NoSQL database
    :cvar API: External API
    :cvar FILE_SYSTEM: Local or network file system
    """
    SHAREPOINT = "sharepoint"
    ONEDRIVE = "onedrive"
    GDRIVE = "gdrive"
    S3 = "s3"
    DATABASE = "database"
    API = "api"
    FILE_SYSTEM = "file_system"


@json_schema_type
class Document(BaseModel):
    """Document in the knowledge base.
    
    :param document_id: Unique identifier for the document
    :param title: Title of the document
    :param content: Content of the document
    :param document_type: Type of document
    :param metadata: Additional metadata for the document
    :param status: Processing status of the document
    :param created_at: Time when the document was created
    :param updated_at: Time when the document was last updated
    :param source_url: URL of the original document
    :param access_control: Access control settings for the document
    """
    document_id: str
    title: str
    content: Optional[InterleavedContent] = None
    document_type: DocumentType
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: str
    updated_at: str
    source_url: Optional[URL] = None
    access_control: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class DataSourceConfig(BaseModel):
    """Configuration for an enterprise data source.
    
    :param source_id: Unique identifier for the data source
    :param name: Name of the data source
    :param source_type: Type of data source
    :param connection_params: Parameters for connecting to the data source
    :param sync_schedule: Schedule for synchronizing with the data source
    :param filters: Filters for selecting documents from the data source
    :param metadata: Additional metadata for the data source
    """
    source_id: str
    name: str
    source_type: DataSourceType
    connection_params: Dict[str, Any]
    sync_schedule: Optional[str] = None
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class KnowledgeBase(BaseModel):
    """Knowledge base for storing and retrieving documents.
    
    :param kb_id: Unique identifier for the knowledge base
    :param name: Name of the knowledge base
    :param description: Description of the knowledge base
    :param vector_db_id: ID of the vector database used for storage
    :param embedding_model: Model used for generating embeddings
    :param metadata: Additional metadata for the knowledge base
    :param created_at: Time when the knowledge base was created
    :param updated_at: Time when the knowledge base was last updated
    :param access_control: Access control settings for the knowledge base
    """
    kb_id: str
    name: str
    description: Optional[str] = None
    vector_db_id: str
    embedding_model: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    access_control: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class SyncStatus(BaseModel):
    """Status of a data source synchronization.
    
    :param sync_id: Unique identifier for the sync operation
    :param source_id: ID of the data source
    :param kb_id: ID of the knowledge base
    :param status: Status of the sync operation
    :param started_at: Time when the sync started
    :param completed_at: Time when the sync completed
    :param documents_processed: Number of documents processed
    :param documents_failed: Number of documents that failed processing
    :param error_message: Error message if the sync failed
    """
    sync_id: str
    source_id: str
    kb_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    documents_processed: int = 0
    documents_failed: int = 0
    error_message: Optional[str] = None


@json_schema_type
class SearchResult(BaseModel):
    """Result of a search query.
    
    :param document_id: ID of the document
    :param title: Title of the document
    :param content: Relevant content from the document
    :param score: Relevance score
    :param metadata: Additional metadata for the document
    """
    document_id: str
    title: str
    content: InterleavedContent
    score: float
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class SearchResponse(BaseModel):
    """Response from a search query.
    
    :param results: List of search results
    :param total_results: Total number of results
    :param query: Original query
    """
    results: List[SearchResult]
    total_results: int
    query: str


@runtime_checkable
@trace_protocol
class EnterpriseKnowledge(Protocol):
    """Llama Stack Enterprise Knowledge API for connecting to enterprise document systems.
    
    This API provides enterprise-grade knowledge management capabilities for Llama Stack:
    - Connect to enterprise document repositories (SharePoint, OneDrive, etc.)
    - Process and index documents for retrieval
    - Search and retrieve documents with access control
    - Synchronize with enterprise data sources
    """
    
    @webmethod(route="/enterprise/knowledge/bases", method="POST")
    async def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        vector_db_id: Optional[str] = None,
        embedding_model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_control: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeBase:
        """Create a new knowledge base.
        
        :param name: Name of the knowledge base
        :param description: Description of the knowledge base
        :param vector_db_id: ID of the vector database to use
        :param embedding_model: Model to use for generating embeddings
        :param metadata: Additional metadata for the knowledge base
        :param access_control: Access control settings for the knowledge base
        :returns: Created knowledge base
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/bases/{kb_id}", method="GET")
    async def get_knowledge_base(
        self,
        kb_id: str,
    ) -> KnowledgeBase:
        """Get a knowledge base by ID.
        
        :param kb_id: ID of the knowledge base
        :returns: Knowledge base
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/bases/{kb_id}", method="PUT")
    async def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        vector_db_id: Optional[str] = None,
        embedding_model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_control: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeBase:
        """Update a knowledge base.
        
        :param kb_id: ID of the knowledge base
        :param name: Name of the knowledge base
        :param description: Description of the knowledge base
        :param vector_db_id: ID of the vector database to use
        :param embedding_model: Model to use for generating embeddings
        :param metadata: Additional metadata for the knowledge base
        :param access_control: Access control settings for the knowledge base
        :returns: Updated knowledge base
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/bases/{kb_id}", method="DELETE")
    async def delete_knowledge_base(
        self,
        kb_id: str,
    ) -> None:
        """Delete a knowledge base.
        
        :param kb_id: ID of the knowledge base
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/bases/{kb_id}/documents", method="POST")
    async def add_document(
        self,
        kb_id: str,
        title: str,
        content: Optional[InterleavedContent] = None,
        document_type: DocumentType = DocumentType.TXT,
        metadata: Optional[Dict[str, Any]] = None,
        source_url: Optional[URL] = None,
        access_control: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Add a document to a knowledge base.
        
        :param kb_id: ID of the knowledge base
        :param title: Title of the document
        :param content: Content of the document
        :param document_type: Type of document
        :param metadata: Additional metadata for the document
        :param source_url: URL of the original document
        :param access_control: Access control settings for the document
        :returns: Added document
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/bases/{kb_id}/documents/{document_id}", method="GET")
    async def get_document(
        self,
        kb_id: str,
        document_id: str,
    ) -> Document:
        """Get a document from a knowledge base.
        
        :param kb_id: ID of the knowledge base
        :param document_id: ID of the document
        :returns: Document
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/bases/{kb_id}/documents/{document_id}", method="PUT")
    async def update_document(
        self,
        kb_id: str,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[InterleavedContent] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_control: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Update a document in a knowledge base.
        
        :param kb_id: ID of the knowledge base
        :param document_id: ID of the document
        :param title: Title of the document
        :param content: Content of the document
        :param metadata: Additional metadata for the document
        :param access_control: Access control settings for the document
        :returns: Updated document
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/bases/{kb_id}/documents/{document_id}", method="DELETE")
    async def delete_document(
        self,
        kb_id: str,
        document_id: str,
    ) -> None:
        """Delete a document from a knowledge base.
        
        :param kb_id: ID of the knowledge base
        :param document_id: ID of the document
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/bases/{kb_id}/search", method="POST")
    async def search(
        self,
        kb_id: str,
        query: str,
        limit: Optional[int] = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResponse:
        """Search a knowledge base.
        
        :param kb_id: ID of the knowledge base
        :param query: Search query
        :param limit: Maximum number of results to return
        :param filters: Filters to apply to the search
        :returns: Search results
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/sources", method="POST")
    async def create_data_source(
        self,
        name: str,
        source_type: DataSourceType,
        connection_params: Dict[str, Any],
        sync_schedule: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DataSourceConfig:
        """Create a new data source.
        
        :param name: Name of the data source
        :param source_type: Type of data source
        :param connection_params: Parameters for connecting to the data source
        :param sync_schedule: Schedule for synchronizing with the data source
        :param filters: Filters for selecting documents from the data source
        :param metadata: Additional metadata for the data source
        :returns: Created data source
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/sources/{source_id}", method="GET")
    async def get_data_source(
        self,
        source_id: str,
    ) -> DataSourceConfig:
        """Get a data source by ID.
        
        :param source_id: ID of the data source
        :returns: Data source
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/sources/{source_id}", method="PUT")
    async def update_data_source(
        self,
        source_id: str,
        name: Optional[str] = None,
        connection_params: Optional[Dict[str, Any]] = None,
        sync_schedule: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DataSourceConfig:
        """Update a data source.
        
        :param source_id: ID of the data source
        :param name: Name of the data source
        :param connection_params: Parameters for connecting to the data source
        :param sync_schedule: Schedule for synchronizing with the data source
        :param filters: Filters for selecting documents from the data source
        :param metadata: Additional metadata for the data source
        :returns: Updated data source
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/sources/{source_id}", method="DELETE")
    async def delete_data_source(
        self,
        source_id: str,
    ) -> None:
        """Delete a data source.
        
        :param source_id: ID of the data source
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/sync", method="POST")
    async def sync_data_source(
        self,
        source_id: str,
        kb_id: str,
    ) -> SyncStatus:
        """Synchronize a data source with a knowledge base.
        
        :param source_id: ID of the data source
        :param kb_id: ID of the knowledge base
        :returns: Sync status
        """
        ...
    
    @webmethod(route="/enterprise/knowledge/sync/{sync_id}", method="GET")
    async def get_sync_status(
        self,
        sync_id: str,
    ) -> SyncStatus:
        """Get the status of a data source synchronization.
        
        :param sync_id: ID of the sync operation
        :returns: Sync status
        """
        ...
