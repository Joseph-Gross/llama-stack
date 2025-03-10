# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
import base64
import io
import ipaddress
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse

import chardet
import httpx
import numpy as np
from llama_models.llama3.api.tokenizer import Tokenizer
from numpy.typing import NDArray
from pypdf import PdfReader

from llama_stack.apis.common.content_types import (
    URL,
    InterleavedContent,
    TextContentItem,
)
from llama_stack.apis.tools import RAGDocument
from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk, QueryChunksResponse
from llama_stack.providers.datatypes import Api
from llama_stack.providers.utils.inference.prompt_adapter import (
    interleaved_content_as_str,
)

log = logging.getLogger(__name__)


def _is_safe_url(url: str) -> bool:
    """Validate URL for safety.
    
    Checks:
    1. URL scheme is allowed (http, https, data, file)
    2. No localhost or internal IP addresses for remote URLs
    3. Basic format validation
    """
    if url.startswith("data:"):
        # Data URLs are handled separately with content validation
        return True
        
    allowed_schemes = ["http://", "https://", "file://"]
    if not any(url.startswith(scheme) for scheme in allowed_schemes):
        return False
        
    # Block localhost and private IPs for remote URLs
    if url.startswith(("http://", "https://")):
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc.split(":", 1)[0]
        
        if hostname in ["localhost", "127.0.0.1", "::1"]:
            return False
            
        # Check for private IP ranges
        try:
            if hostname.replace(".", "").isdigit():  # IPv4 check
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_reserved:
                    return False
        except ValueError:
            # Not a valid IP address, continue with hostname checks
            pass
            
    return True


def parse_pdf(data: bytes) -> str:
    # For PDF and DOC/DOCX files, we can't reliably convert to string
    pdf_bytes = io.BytesIO(data)
    pdf_reader = PdfReader(pdf_bytes)
    return "\n".join([page.extract_text() for page in pdf_reader.pages])


def parse_data_url(data_url: str):
    data_url_pattern = re.compile(
        r"^"
        r"data:"
        r"(?P<mimetype>[\w/\-+.]+)"
        r"(?P<charset>;charset=(?P<encoding>[\w-]+))?"
        r"(?P<base64>;base64)?"
        r",(?P<data>.*)"
        r"$",
        re.DOTALL,
    )
    match = data_url_pattern.match(data_url)
    if not match:
        raise ValueError("Invalid Data URL format")

    parts = match.groupdict()
    parts["is_base64"] = bool(parts["base64"])
    return parts


def content_from_data(data_url: str) -> str:
    parts = parse_data_url(data_url)
    data = parts["data"]

    if parts["is_base64"]:
        data = base64.b64decode(data)
    else:
        data = unquote(data)
        encoding = parts["encoding"] or "utf-8"
        data = data.encode(encoding)

    encoding = parts["encoding"]
    if not encoding:
        detected = chardet.detect(data)
        encoding = detected["encoding"]

    mime_type = parts["mimetype"]
    mime_category = mime_type.split("/")[0]
    if mime_category == "text":
        # For text-based files (including CSV, MD)
        return data.decode(encoding)

    elif mime_type == "application/pdf":
        return parse_pdf(data)

    else:
        log.error("Could not extract content from data_url properly.")
        return ""


def concat_interleaved_content(content: List[InterleavedContent]) -> InterleavedContent:
    """concatenate interleaved content into a single list. ensure that 'str's are converted to TextContentItem when in a list"""

    ret = []

    def _process(c):
        if isinstance(c, str):
            ret.append(TextContentItem(text=c))
        elif isinstance(c, list):
            for item in c:
                _process(item)
        else:
            ret.append(c)

    for c in content:
        _process(c)

    return ret


async def content_from_doc(doc: RAGDocument) -> str:
    # Validate URL before processing
    if isinstance(doc.content, URL):
        url = doc.content.uri
        # Validate URL format and scheme
        if not _is_safe_url(url):
            raise ValueError(f"Unsafe URL provided: {url}")
            
        if url.startswith("data:"):
            return content_from_data(url)
        else:
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(url, timeout=10.0, follow_redirects=True)
                    r.raise_for_status()  # Raise exception for 4XX/5XX responses
                except httpx.HTTPError as e:
                    log.error(f"Error fetching URL {url}: {str(e)}")
                    raise ValueError(f"Error fetching URL: {str(e)}")
            if doc.mime_type == "application/pdf":
                return parse_pdf(r.content)
            else:
                return r.text

    pattern = re.compile("^(https?://|file://|data:)")
    if pattern.match(doc.content):
        url = doc.content
        # Validate URL format and scheme
        if not _is_safe_url(url):
            raise ValueError(f"Unsafe URL provided: {url}")
            
        if url.startswith("data:"):
            return content_from_data(url)
        else:
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(url, timeout=10.0, follow_redirects=True)
                    r.raise_for_status()  # Raise exception for 4XX/5XX responses
                except httpx.HTTPError as e:
                    log.error(f"Error fetching URL {url}: {str(e)}")
                    raise ValueError(f"Error fetching URL: {str(e)}")
            if doc.mime_type == "application/pdf":
                return parse_pdf(r.content)
            else:
                return r.text

    return interleaved_content_as_str(doc.content)


def make_overlapped_chunks(document_id: str, text: str, window_len: int, overlap_len: int) -> List[Chunk]:
    tokenizer = Tokenizer.get_instance()
    tokens = tokenizer.encode(text, bos=False, eos=False)

    chunks = []
    for i in range(0, len(tokens), window_len - overlap_len):
        toks = tokens[i : i + window_len]
        chunk = tokenizer.decode(toks)
        # chunk is a string
        chunks.append(
            Chunk(
                content=chunk,
                metadata={
                    "token_count": len(toks),
                    "document_id": document_id,
                },
            )
        )

    return chunks


class EmbeddingIndex(ABC):
    @abstractmethod
    async def add_chunks(self, chunks: List[Chunk], embeddings: NDArray):
        raise NotImplementedError()

    @abstractmethod
    async def query(self, embedding: NDArray, k: int, score_threshold: float) -> QueryChunksResponse:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self):
        raise NotImplementedError()


@dataclass
class VectorDBWithIndex:
    vector_db: VectorDB
    index: EmbeddingIndex
    inference_api: Api.inference

    async def insert_chunks(
        self,
        chunks: List[Chunk],
    ) -> None:
        embeddings_response = await self.inference_api.embeddings(
            self.vector_db.embedding_model, [x.content for x in chunks]
        )
        embeddings = np.array(embeddings_response.embeddings)

        await self.index.add_chunks(chunks, embeddings)

    async def query_chunks(
        self,
        query: InterleavedContent,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryChunksResponse:
        if params is None:
            params = {}
        k = params.get("max_chunks", 3)
        score_threshold = params.get("score_threshold", 0.0)

        query_str = interleaved_content_as_str(query)
        embeddings_response = await self.inference_api.embeddings(self.vector_db.embedding_model, [query_str])
        query_vector = np.array(embeddings_response.embeddings[0], dtype=np.float32)
        return await self.index.query(query_vector, k, score_threshold)
