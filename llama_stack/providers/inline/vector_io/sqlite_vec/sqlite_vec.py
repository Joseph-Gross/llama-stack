# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import hashlib
import logging
import sqlite3
import struct
import uuid
from typing import Any, Dict, List, Optional

import numpy as np
import sqlite_vec
from numpy.typing import NDArray

from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk, QueryChunksResponse, VectorIO
from llama_stack.providers.datatypes import VectorDBsProtocolPrivate
from llama_stack.providers.utils.memory.vector_store import EmbeddingIndex, VectorDBWithIndex

logger = logging.getLogger(__name__)


def serialize_vector(vector: List[float]) -> bytes:
    """Serialize a list of floats into a compact binary representation."""
    return struct.pack(f"{len(vector)}f", *vector)


class SQLiteVecIndex(EmbeddingIndex):
    """
    An index implementation that stores embeddings in a SQLite virtual table using sqlite-vec.
    Two tables are used:
      - A metadata table (chunks_{bank_id}) that holds the chunk JSON.
      - A virtual table (vec_chunks_{bank_id}) that holds the serialized vector.
    """

    def __init__(self, dimension: int, connection: sqlite3.Connection, bank_id: str):
        self.dimension = dimension
        self.connection = connection
        self.bank_id = bank_id
        self.metadata_table = f"chunks_{bank_id}".replace("-", "_")
        self.vector_table = f"vec_chunks_{bank_id}".replace("-", "_")

    @classmethod
    async def create(cls, dimension: int, connection: sqlite3.Connection, bank_id: str):
        instance = cls(dimension, connection, bank_id)
        await instance.initialize()
        return instance

    async def initialize(self) -> None:
        cur = self.connection.cursor()
        # Create the table to store chunk metadata.
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.metadata_table} (
                id TEXT PRIMARY KEY,
                chunk TEXT
            );
        """)
        # Create the virtual table for embeddings.
        cur.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.vector_table}
            USING vec0(embedding FLOAT[{self.dimension}], id TEXT);
        """)
        self.connection.commit()

    async def delete(self):
        cur = self.connection.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.metadata_table};")
        cur.execute(f"DROP TABLE IF EXISTS {self.vector_table};")
        self.connection.commit()

    async def add_chunks(self, chunks: List[Chunk], embeddings: NDArray, batch_size: int = 500):
        """
        Add new chunks along with their embeddings using batch inserts.
        For each chunk, we insert its JSON into the metadata table and then insert its
        embedding (serialized to raw bytes) into the virtual table using the assigned rowid.
        If any insert fails, the transaction is rolled back to maintain consistency.
        """
        cur = self.connection.cursor()
        try:
            # Start transaction
            cur.execute("BEGIN TRANSACTION")
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i : i + batch_size]
                batch_embeddings = embeddings[i : i + batch_size]
                # Prepare metadata inserts
                metadata_data = [
                    (generate_chunk_id(chunk.metadata["document_id"], chunk.content), chunk.model_dump_json())
                    for chunk in batch_chunks
                ]
                # Insert metadata (ON CONFLICT to avoid duplicates)
                cur.executemany(
                    f"""
                    INSERT INTO {self.metadata_table} (id, chunk)
                    VALUES (?, ?)
                    ON CONFLICT(id) DO UPDATE SET chunk = excluded.chunk;
                    """,
                    metadata_data,
                )
                # Prepare embeddings inserts
                embedding_data = [
                    (generate_chunk_id(chunk.metadata["document_id"], chunk.content), serialize_vector(emb.tolist()))
                    for chunk, emb in zip(batch_chunks, batch_embeddings, strict=True)
                ]
                # Insert embeddings in batch
                cur.executemany(f"INSERT INTO {self.vector_table} (id, embedding) VALUES (?, ?);", embedding_data)
            self.connection.commit()

        except sqlite3.Error as e:
            self.connection.rollback()  # Rollback on failure
            logger.error(f"Error inserting into {self.vector_table}: {e}")

        finally:
            cur.close()  # Ensure cursor is closed

    async def query(self, embedding: NDArray, k: int, score_threshold: float) -> QueryChunksResponse:
        """
        Query for the k most similar chunks. We convert the query embedding to a blob and run a SQL query
        against the virtual table. The SQL joins the metadata table to recover the chunk JSON.
        """
        cur = None
        try:
            # Convert embedding to list format regardless of input type
            if isinstance(embedding, np.ndarray):
                emb_list = embedding.tolist()
            elif hasattr(embedding, 'tolist'):
                emb_list = embedding.tolist()
            else:
                # Convert any iterable to a list of floats
                emb_list = [float(x) for x in list(embedding)]
                
            # Ensure we have a list of floats for serialization
            try:
                # Convert each element individually to handle mixed types
                float_list = []
                for val in emb_list:
                    try:
                        # Explicitly convert to float with a safer approach
                        if isinstance(val, (int, float)):
                            float_list.append(float(val))
                        elif isinstance(val, str):
                            float_list.append(float(val.strip()))
                        else:
                            # For other types, use fallback
                            float_list.append(0.0)
                    except (ValueError, TypeError):
                        # If conversion fails, use 0.0 as a fallback
                        float_list.append(0.0)
            except Exception as e:
                logger.error(f"Error converting embedding values to float: {e}")
                # Fallback to empty list with proper dimension
                float_list = [0.0] * self.dimension
                
            # Serialize the vector for SQLite
            emb_blob = serialize_vector(float_list)
            
            cur = self.connection.cursor()
            query_sql = f"""
                SELECT m.id, m.chunk, v.distance
                FROM {self.vector_table} AS v
                JOIN {self.metadata_table} AS m ON m.id = v.id
                WHERE v.embedding MATCH ? AND k = ?
                ORDER BY v.distance;
            """
            cur.execute(query_sql, (emb_blob, k))
            rows = cur.fetchall()
            chunks = []
            scores = []
            for _id, chunk_json, distance in rows:
                try:
                    chunk = Chunk.model_validate_json(chunk_json)
                except Exception as e:
                    logger.error(f"Error parsing chunk JSON for id {_id}: {e}")
                    continue
                chunks.append(chunk)
                # Mimic the Faiss scoring: score = 1/distance (avoid division by zero)
                score = 1.0 / distance if distance != 0 else float("inf")
                scores.append(score)
            return QueryChunksResponse(chunks=chunks, scores=scores)
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error during vector query: {e}")
            return QueryChunksResponse(chunks=[], scores=[])
        except Exception as e:
            logger.error(f"Unexpected error during vector query: {e}")
            return QueryChunksResponse(chunks=[], scores=[])
        finally:
            if cur:
                cur.close()


class SQLiteVecVectorIOAdapter(VectorIO, VectorDBsProtocolPrivate):
    """
    A VectorIO implementation using SQLite + sqlite_vec.
    This class handles vector database registration (with metadata stored in a table named `vector_dbs`)
    and creates a cache of VectorDBWithIndex instances (each wrapping a SQLiteVecIndex).
    """

    def __init__(self, config, inference_api: Any) -> None:
        self.config = config
        self.inference_api = inference_api
        self.cache: Dict[str, VectorDBWithIndex] = {}
        self.connection: Optional[sqlite3.Connection] = None

    async def initialize(self) -> None:
        cur = None
        try:
            # Open a connection to the SQLite database (the file is specified in the config).
            if not hasattr(self.config, 'db_path') or not self.config.db_path:
                logger.error("Missing db_path in configuration")
                raise ValueError("Missing db_path in configuration")
                
            self.connection = sqlite3.connect(self.config.db_path)
            self.connection.enable_load_extension(True)
            
            # Load the sqlite_vec extension - method may vary based on the library implementation
            try:
                # Dynamically access the load method to avoid static type checking issues
                load_method = getattr(sqlite_vec, 'load', None)
                if load_method is not None and callable(load_method):
                    load_method(self.connection)
                else:
                    # Fallback to SQL initialization
                    self.connection.execute("SELECT sqlite_vec_init()")
            except Exception as e:
                logger.warning(f"Error loading sqlite_vec extension: {e}")
                # Last resort fallback
                self.connection.execute("SELECT sqlite_vec_init()")
                
            self.connection.enable_load_extension(False)
            cur = self.connection.cursor()
            
            # Create a table to persist vector DB registrations.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vector_dbs (
                    id TEXT PRIMARY KEY,
                    metadata TEXT
                );
            """)
            self.connection.commit()
            
            # Load any existing vector DB registrations.
            cur.execute("SELECT metadata FROM vector_dbs")
            rows = cur.fetchall()
            for row in rows:
                try:
                    vector_db_data = row[0]
                    vector_db = VectorDB.model_validate_json(vector_db_data)
                    index = await SQLiteVecIndex.create(vector_db.embedding_dimension, self.connection, vector_db.identifier)
                    self.cache[vector_db.identifier] = VectorDBWithIndex(vector_db, index, self.inference_api)
                except Exception as e:
                    logger.error(f"Error loading vector DB: {e}")
                    # Continue loading other DBs even if one fails
                    continue
                    
        except sqlite3.Error as e:
            logger.error(f"SQLite error during initialization: {e}")
            raise RuntimeError(f"Failed to initialize SQLite database: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}")
            raise RuntimeError(f"Failed to initialize vector database: {e}")
        finally:
            if cur:
                cur.close()

    async def shutdown(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    async def register_vector_db(self, vector_db: VectorDB) -> None:
        cur = None
        try:
            if self.connection is None:
                logger.error("SQLite connection not initialized")
                raise RuntimeError("SQLite connection not initialized")
                
            if not vector_db or not vector_db.identifier:
                logger.error("Invalid vector DB provided for registration")
                raise ValueError("Invalid vector DB provided for registration")
                
            cur = self.connection.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO vector_dbs (id, metadata) VALUES (?, ?)",
                (vector_db.identifier, vector_db.model_dump_json()),
            )
            self.connection.commit()
            
            index = await SQLiteVecIndex.create(vector_db.embedding_dimension, self.connection, vector_db.identifier)
            self.cache[vector_db.identifier] = VectorDBWithIndex(vector_db, index, self.inference_api)
            logger.info(f"Successfully registered vector DB: {vector_db.identifier}")
            
        except sqlite3.Error as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"SQLite error registering vector DB {vector_db.identifier}: {e}")
            raise RuntimeError(f"Failed to register vector DB: {e}")
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Error registering vector DB {vector_db.identifier}: {e}")
            raise
        finally:
            if cur:
                cur.close()

    async def list_vector_dbs(self) -> List[VectorDB]:
        try:
            if not self.connection:
                logger.error("SQLite connection not initialized")
                return []
                
            return [v.vector_db for v in self.cache.values()]
        except Exception as e:
            logger.error(f"Error listing vector DBs: {e}")
            return []

    async def unregister_vector_db(self, vector_db_id: str) -> None:
        cur = None
        try:
            if self.connection is None:
                logger.error("SQLite connection not initialized")
                raise RuntimeError("SQLite connection not initialized")
                
            if not vector_db_id:
                logger.error("Invalid vector DB ID provided for unregistration")
                raise ValueError("Invalid vector DB ID provided for unregistration")
                
            if vector_db_id not in self.cache:
                logger.warning(f"Vector DB {vector_db_id} not found, nothing to unregister")
                return
                
            # Delete the index first
            try:
                await self.cache[vector_db_id].index.delete()
            except Exception as e:
                logger.error(f"Error deleting index for vector DB {vector_db_id}: {e}")
                # Continue with unregistration even if index deletion fails
                
            # Remove from cache
            del self.cache[vector_db_id]
            
            # Remove from database
            cur = self.connection.cursor()
            cur.execute("DELETE FROM vector_dbs WHERE id = ?", (vector_db_id,))
            self.connection.commit()
            logger.info(f"Successfully unregistered vector DB: {vector_db_id}")
            
        except sqlite3.Error as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"SQLite error unregistering vector DB {vector_db_id}: {e}")
            raise RuntimeError(f"Failed to unregister vector DB: {e}")
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Error unregistering vector DB {vector_db_id}: {e}")
            raise
        finally:
            if cur:
                cur.close()

    async def insert_chunks(self, vector_db_id: str, chunks: List[Chunk], ttl_seconds: Optional[int] = None) -> None:
        try:
            if not self.connection:
                logger.error("SQLite connection not initialized")
                raise RuntimeError("SQLite connection not initialized")
                
            if not chunks:
                logger.warning(f"No chunks provided to insert into vector DB {vector_db_id}")
                return
                
            if vector_db_id not in self.cache:
                available_dbs = list(self.cache.keys())
                logger.error(f"Vector DB {vector_db_id} not found. Available DBs: {available_dbs}")
                raise ValueError(f"Vector DB {vector_db_id} not found. Available DBs: {available_dbs}")
                
            # The VectorDBWithIndex helper is expected to compute embeddings via the inference_api
            # and then call our index's add_chunks.
            await self.cache[vector_db_id].insert_chunks(chunks)
            
        except Exception as e:
            logger.error(f"Error inserting chunks into vector DB {vector_db_id}: {e}")
            raise

    async def query_chunks(
        self, vector_db_id: str, query: Any, params: Optional[Dict[str, Any]] = None
    ) -> QueryChunksResponse:
        try:
            if not self.connection:
                logger.error("SQLite connection not initialized")
                return QueryChunksResponse(chunks=[], scores=[])
                
            if vector_db_id not in self.cache:
                logger.error(f"Vector DB {vector_db_id} not found. Available DBs: {list(self.cache.keys())}")
                return QueryChunksResponse(chunks=[], scores=[])
                
            return await self.cache[vector_db_id].query_chunks(query, params)
            
        except Exception as e:
            logger.error(f"Error querying chunks from vector DB {vector_db_id}: {e}")
            return QueryChunksResponse(chunks=[], scores=[])


def generate_chunk_id(document_id: str, chunk_text: str) -> str:
    """Generate a unique chunk ID using a hash of document ID and chunk text."""
    hash_input = f"{document_id}:{chunk_text}".encode("utf-8")
    return str(uuid.UUID(hashlib.md5(hash_input).hexdigest()))
