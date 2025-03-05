"""
# Research Workflow Example with Llama Stack

This notebook demonstrates a complete research workflow using Llama Stack,
focusing on reproducibility, documentation, and best practices for research code.

## Setup and Imports
"""

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional

import numpy as np
import matplotlib.pyplot as plt

from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk
from llama_stack.utils.random_utils import set_random_seed, get_numpy_random_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("research_workflow")

"""
## 1. Experiment Configuration

First, we define our experiment configuration with all parameters explicitly documented.
"""

class ExperimentConfig:
    """Configuration for the research experiment."""
    
    def __init__(self, seed: int = 42):
        # General settings
        self.seed = seed
        self.experiment_name = "document_similarity_analysis"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Data settings
        self.num_documents = 5
        self.chunks_per_document = 3
        self.embedding_dimension = 384
        self.embedding_model = "all-MiniLM-L6-v2"
        
        # Vector database settings
        self.vector_db_provider = "sqlite_vec"
        self.vector_db_id = f"research_{self.timestamp}"
        
        # Query settings
        self.num_queries = 3
        self.k_values = [1, 3, 5, 10]
        self.score_thresholds = [0.0, 0.5, 0.7, 0.9]
        
        # Output settings
        self.results_dir = "results"
        self.save_embeddings = True
        self.save_queries = True
        self.save_results = True
        self.generate_plots = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary for serialization."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def save(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved experiment configuration to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'ExperimentConfig':
        """Load configuration from a JSON file."""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        config = cls()
        for key, value in config_dict.items():
            setattr(config, key, value)
        
        logger.info(f"Loaded experiment configuration from {filepath}")
        return config

"""
## 2. Data Generation

Next, we generate synthetic data for our experiment, ensuring reproducibility.
"""

def generate_research_documents(config: ExperimentConfig) -> List[Dict[str, Any]]:
    """Generate synthetic research documents for the experiment."""
    # Set seed for reproducibility
    set_random_seed(config.seed)
    rng = get_numpy_random_generator(config.seed)
    
    # Define research topics
    topics = [
        "Machine Learning",
        "Natural Language Processing",
        "Computer Vision",
        "Reinforcement Learning",
        "Neural Networks"
    ]
    
    # Generate documents
    documents = []
    for i in range(config.num_documents):
        topic = topics[i % len(topics)]
        
        # Generate document metadata
        document = {
            "id": f"doc-{i}",
            "title": f"Research on {topic}",
            "author": f"Researcher {i % 3 + 1}",
            "year": 2020 + (i % 5),
            "topic": topic,
            "chunks": []
        }
        
        # Generate chunks for this document
        for j in range(config.chunks_per_document):
            chunk_text = f"This is chunk {j} of document {i} about {topic}. "
            chunk_text += f"It contains important research findings about {topic}. "
            chunk_text += f"The research was conducted in {document['year']} by {document['author']}."
            
            chunk = {
                "content": chunk_text,
                "metadata": {
                    "document_id": document["id"],
                    "chunk_index": j,
                    "topic": topic,
                    "importance": rng.integers(1, 6)  # 1-5 importance score
                }
            }
            document["chunks"].append(chunk)
        
        documents.append(document)
    
    logger.info(f"Generated {len(documents)} documents with {config.chunks_per_document} chunks each")
    return documents

def generate_query_embeddings(config: ExperimentConfig) -> List[np.ndarray]:
    """Generate query embeddings for the experiment."""
    # Set seed for reproducibility
    rng = get_numpy_random_generator(config.seed + 1)  # Different seed for queries
    
    # Generate query embeddings
    query_embeddings = []
    for i in range(config.num_queries):
        # Generate a random embedding
        embedding = rng.random(config.embedding_dimension).astype(np.float32)
        # Normalize the embedding
        embedding = embedding / np.linalg.norm(embedding)
        query_embeddings.append(embedding)
    
    logger.info(f"Generated {len(query_embeddings)} query embeddings")
    return query_embeddings

"""
## 3. Vector Database Setup

Now we set up the vector database for our experiment.
"""

async def setup_vector_database(config: ExperimentConfig) -> Any:
    """Set up a vector database for the experiment."""
    # Import here to avoid circular imports
    from llama_stack.providers.inline.vector_io.sqlite_vec.sqlite_vec import (
        SQLiteVecVectorIOAdapter,
    )
    
    # Create a temporary database file
    db_path = os.path.join(tempfile.gettempdir(), f"{config.vector_db_id}.db")
    
    # Create a configuration object
    adapter_config = type("Config", (object,), {"db_path": db_path})
    
    # Create a mock inference API
    inference_api = type("InferenceAPI", (object,), {
        "embed_text": lambda texts, model: np.random.rand(len(texts), config.embedding_dimension).astype(np.float32)
    })
    
    # Create and initialize the adapter
    # Note: In a real application, you would use a concrete implementation
    # For this example, we'll create a mock adapter
    from unittest.mock import MagicMock, AsyncMock
    
    adapter = MagicMock(spec=SQLiteVecVectorIOAdapter)
    adapter.initialize = AsyncMock()
    adapter.shutdown = AsyncMock()
    adapter.register_vector_db = AsyncMock()
    adapter.cache = {}  # Mock cache for vector DB storage
    
    await adapter.initialize()
    
    # Register a vector database
    vector_db = VectorDB(
        identifier=config.vector_db_id,
        embedding_model=config.embedding_model,
        embedding_dimension=config.embedding_dimension,
        metadata={"experiment": config.experiment_name, "seed": config.seed},
        provider_id=config.vector_db_provider,
    )
    
    await adapter.register_vector_db(vector_db)
    logger.info(f"Set up vector database '{config.vector_db_id}'")
    
    return adapter

"""
## 4. Document Processing and Embedding

Next, we process the documents and generate embeddings.
"""

def convert_to_chunks(documents: List[Dict[str, Any]]) -> List[Chunk]:
    """Convert document chunks to Chunk objects."""
    chunks = []
    for document in documents:
        for chunk_data in document["chunks"]:
            chunk = Chunk(
                content=chunk_data["content"],
                metadata=chunk_data["metadata"]
            )
            chunks.append(chunk)
    
    logger.info(f"Converted {len(chunks)} document chunks to Chunk objects")
    return chunks

def generate_chunk_embeddings(chunks: List[Chunk], config: ExperimentConfig) -> np.ndarray:
    """Generate embeddings for chunks."""
    # Set seed for reproducibility
    rng = get_numpy_random_generator(config.seed)
    
    # Generate embeddings
    embeddings = np.array([
        rng.random(config.embedding_dimension).astype(np.float32)
        for _ in range(len(chunks))
    ])
    
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized_embeddings = embeddings / norms
    
    logger.info(f"Generated {len(normalized_embeddings)} chunk embeddings")
    return normalized_embeddings

async def insert_chunks_with_embeddings(
    adapter: Any,
    vector_db_id: str,
    chunks: List[Chunk],
    embeddings: np.ndarray
) -> None:
    """Insert chunks and embeddings into the vector database."""
    # Get the vector DB with index from the adapter's cache
    vector_db_with_index = adapter.cache[vector_db_id]
    
    # Add chunks and embeddings to the index
    await vector_db_with_index.index.add_chunks(chunks, embeddings)
    
    logger.info(f"Inserted {len(chunks)} chunks into vector database '{vector_db_id}'")

"""
## 5. Experiment Execution

Now we run the experiment with different parameters.
"""

async def run_queries(
    adapter: Any,
    vector_db_id: str,
    query_embeddings: List[np.ndarray],
    k_values: List[int],
    score_thresholds: List[float]
) -> Dict[str, Any]:
    """Run queries with different parameters and collect results."""
    results = {
        "queries": [],
        "parameters": {
            "k_values": k_values,
            "score_thresholds": score_thresholds
        }
    }
    
    # Get the vector DB with index from the adapter's cache
    vector_db_with_index = adapter.cache[vector_db_id]
    
    # Run queries with different parameters
    for i, query_embedding in enumerate(query_embeddings):
        query_results = {
            "query_id": i,
            "embedding": query_embedding.tolist(),
            "results": []
        }
        
        for k in k_values:
            for threshold in score_thresholds:
                # Query the index
                response = await vector_db_with_index.index.query(
                    embedding=query_embedding,
                    k=k,
                    score_threshold=threshold
                )
                
                # Record results
                parameter_results = {
                    "k": k,
                    "score_threshold": threshold,
                    "num_results": len(response.chunks),
                    "chunks": [
                        {
                            "content": chunk.content,
                            "metadata": chunk.metadata,
                            "score": score
                        }
                        for chunk, score in zip(response.chunks, response.scores)
                    ]
                }
                
                query_results["results"].append(parameter_results)
        
        results["queries"].append(query_results)
    
    logger.info(f"Ran {len(query_embeddings)} queries with {len(k_values) * len(score_thresholds)} parameter combinations")
    return results

"""
## 6. Results Analysis and Visualization

Now we analyze the results and generate visualizations.
"""

def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze experiment results."""
    analysis = {
        "summary": {},
        "by_parameter": {},
        "by_query": {}
    }
    
    # Extract parameters
    k_values = results["parameters"]["k_values"]
    score_thresholds = results["parameters"]["score_thresholds"]
    
    # Analyze results by parameter combination
    for k in k_values:
        for threshold in score_thresholds:
            key = f"k={k},threshold={threshold}"
            analysis["by_parameter"][key] = {
                "num_results": [],
                "avg_score": []
            }
    
    # Analyze results by query
    for query in results["queries"]:
        query_id = query["query_id"]
        analysis["by_query"][query_id] = {
            "avg_results": 0,
            "max_score": 0,
            "min_score": float('inf'),
            "by_parameter": {}
        }
        
        total_results = 0
        total_params = 0
        
        for param_result in query["results"]:
            k = param_result["k"]
            threshold = param_result["score_threshold"]
            num_results = param_result["num_results"]
            
            # Update by_parameter analysis
            key = f"k={k},threshold={threshold}"
            analysis["by_parameter"][key]["num_results"].append(num_results)
            
            # Calculate average score if there are results
            if num_results > 0:
                avg_score = sum(chunk["score"] for chunk in param_result["chunks"]) / num_results
                analysis["by_parameter"][key]["avg_score"].append(avg_score)
                
                # Update max and min scores
                max_score = max(chunk["score"] for chunk in param_result["chunks"])
                min_score = min(chunk["score"] for chunk in param_result["chunks"])
                
                analysis["by_query"][query_id]["max_score"] = max(analysis["by_query"][query_id]["max_score"], max_score)
                analysis["by_query"][query_id]["min_score"] = min(analysis["by_query"][query_id]["min_score"], min_score)
            
            # Store in query-specific analysis
            analysis["by_query"][query_id]["by_parameter"][key] = {
                "num_results": num_results,
                "avg_score": avg_score if num_results > 0 else 0
            }
            
            total_results += num_results
            total_params += 1
        
        # Calculate average results per parameter
        analysis["by_query"][query_id]["avg_results"] = total_results / total_params if total_params > 0 else 0
        
        # Handle case where no results were found
        if analysis["by_query"][query_id]["min_score"] == float('inf'):
            analysis["by_query"][query_id]["min_score"] = 0
    
    # Calculate overall summary
    total_queries = len(results["queries"])
    total_params = len(k_values) * len(score_thresholds)
    
    # Calculate average number of results across all queries and parameters
    all_num_results = []
    for query in results["queries"]:
        for param_result in query["results"]:
            all_num_results.append(param_result["num_results"])
    
    analysis["summary"]["avg_results_per_query"] = sum(all_num_results) / (total_queries * total_params) if total_queries * total_params > 0 else 0
    analysis["summary"]["total_queries"] = total_queries
    analysis["summary"]["total_parameter_combinations"] = total_params
    
    logger.info("Analyzed experiment results")
    return analysis

def generate_visualizations(results: Dict[str, Any], analysis: Dict[str, Any], config: ExperimentConfig) -> Dict[str, str]:
    """Generate visualizations of experiment results."""
    # Create results directory
    results_dir = os.path.join(config.results_dir, f"{config.experiment_name}_{config.timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    
    visualizations = {}
    
    # 1. Plot number of results by k value and threshold
    plt.figure(figsize=(10, 6))
    
    # Prepare data
    k_values = config.k_values
    thresholds = config.score_thresholds
    
    # Create a matrix of average results
    result_matrix = np.zeros((len(thresholds), len(k_values)))
    
    for i, threshold in enumerate(thresholds):
        for j, k in enumerate(k_values):
            key = f"k={k},threshold={threshold}"
            if key in analysis["by_parameter"]:
                values = analysis["by_parameter"][key]["num_results"]
                result_matrix[i, j] = sum(values) / len(values) if values else 0
    
    # Create heatmap
    plt.imshow(result_matrix, interpolation='nearest', cmap='viridis')
    plt.colorbar(label='Average Number of Results')
    
    # Add labels
    plt.xticks(range(len(k_values)), [str(k) for k in k_values])
    plt.yticks(range(len(thresholds)), [str(t) for t in thresholds])
    plt.xlabel('k Value')
    plt.ylabel('Score Threshold')
    plt.title('Average Number of Results by Parameter Combination')
    
    # Save figure
    heatmap_path = os.path.join(results_dir, 'results_heatmap.png')
    plt.savefig(heatmap_path)
    plt.close()
    
    visualizations['heatmap'] = heatmap_path
    
    # 2. Plot average scores by query
    plt.figure(figsize=(10, 6))
    
    query_ids = list(analysis["by_query"].keys())
    avg_scores = []
    
    for query_id in query_ids:
        # Calculate average score across all parameters
        total_score = 0
        count = 0
        
        for param_key in analysis["by_query"][query_id]["by_parameter"]:
            param_data = analysis["by_query"][query_id]["by_parameter"][param_key]
            if param_data["num_results"] > 0:
                total_score += param_data["avg_score"]
                count += 1
        
        avg_score = total_score / count if count > 0 else 0
        avg_scores.append(avg_score)
    
    plt.bar(range(len(query_ids)), avg_scores)
    plt.xticks(range(len(query_ids)), [f"Query {qid}" for qid in query_ids])
    plt.xlabel('Query')
    plt.ylabel('Average Score')
    plt.title('Average Similarity Score by Query')
    
    # Save figure
    scores_path = os.path.join(results_dir, 'avg_scores_by_query.png')
    plt.savefig(scores_path)
    plt.close()
    
    visualizations['scores'] = scores_path
    
    logger.info(f"Generated visualizations in {results_dir}")
    return visualizations

"""
## 7. Saving and Loading Results

Finally, we save all experiment data for reproducibility and future analysis.
"""

def save_experiment_data(
    config: ExperimentConfig,
    documents: List[Dict[str, Any]],
    chunks: List[Chunk],
    embeddings: np.ndarray,
    query_embeddings: List[np.ndarray],
    results: Dict[str, Any],
    analysis: Dict[str, Any],
    visualizations: Dict[str, str]
) -> str:
    """Save all experiment data for reproducibility."""
    # Create results directory
    results_dir = os.path.join(config.results_dir, f"{config.experiment_name}_{config.timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    
    # Save configuration
    config_path = os.path.join(results_dir, "config.json")
    config.save(config_path)
    
    # Save documents
    documents_path = os.path.join(results_dir, "documents.json")
    with open(documents_path, 'w') as f:
        json.dump(documents, f, indent=2)
    
    # Save chunks (convert to serializable format)
    chunks_path = os.path.join(results_dir, "chunks.json")
    with open(chunks_path, 'w') as f:
        chunks_data = [{"content": chunk.content, "metadata": chunk.metadata} for chunk in chunks]
        json.dump(chunks_data, f, indent=2)
    
    # Save embeddings if configured
    if config.save_embeddings:
        embeddings_path = os.path.join(results_dir, "embeddings.npy")
        np.save(embeddings_path, embeddings)
        
        query_embeddings_path = os.path.join(results_dir, "query_embeddings.npy")
        np.save(query_embeddings_path, np.array(query_embeddings))
    
    # Save results
    results_path = os.path.join(results_dir, "results.json")
    with open(results_path, 'w') as f:
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = json.loads(json.dumps(results, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x))
        json.dump(serializable_results, f, indent=2)
    
    # Save analysis
    analysis_path = os.path.join(results_dir, "analysis.json")
    with open(analysis_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Create a README with experiment summary
    readme_path = os.path.join(results_dir, "README.md")
    with open(readme_path, 'w') as f:
        f.write(f"# {config.experiment_name} Experiment\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Seed: {config.seed}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Documents: {len(documents)}\n")
        f.write(f"- Chunks: {len(chunks)}\n")
        f.write(f"- Queries: {config.num_queries}\n")
        f.write(f"- Parameters: k={config.k_values}, thresholds={config.score_thresholds}\n\n")
        f.write("## Results\n\n")
        f.write(f"- Average results per query: {analysis['summary']['avg_results_per_query']:.2f}\n")
        f.write(f"- Total parameter combinations: {analysis['summary']['total_parameter_combinations']}\n\n")
        f.write("## Visualizations\n\n")
        for name, path in visualizations.items():
            rel_path = os.path.basename(path)
            f.write(f"- [{name.capitalize()}]({rel_path})\n")
    
    logger.info(f"Saved all experiment data to {results_dir}")
    return results_dir

"""
## 8. Complete Research Workflow

Now we put everything together in a complete research workflow.
"""

async def run_research_workflow(config: Optional[ExperimentConfig] = None) -> str:
    """Run the complete research workflow."""
    if config is None:
        config = ExperimentConfig()
    
    try:
        logger.info(f"Starting research workflow: {config.experiment_name}")
        
        # 1. Generate research documents
        documents = generate_research_documents(config)
        
        # 2. Convert to chunks
        chunks = convert_to_chunks(documents)
        
        # 3. Generate embeddings
        embeddings = generate_chunk_embeddings(chunks, config)
        
        # 4. Generate query embeddings
        query_embeddings = generate_query_embeddings(config)
        
        # 5. Set up vector database
        adapter = await setup_vector_database(config)
        
        # 6. Insert chunks and embeddings
        await insert_chunks_with_embeddings(adapter, config.vector_db_id, chunks, embeddings)
        
        # 7. Run queries
        results = await run_queries(
            adapter,
            config.vector_db_id,
            query_embeddings,
            config.k_values,
            config.score_thresholds
        )
        
        # 8. Analyze results
        analysis = analyze_results(results)
        
        # 9. Generate visualizations
        visualizations = generate_visualizations(results, analysis, config)
        
        # 10. Save all experiment data
        results_dir = save_experiment_data(
            config,
            documents,
            chunks,
            embeddings,
            query_embeddings,
            results,
            analysis,
            visualizations
        )
        
        logger.info(f"Research workflow completed successfully")
        logger.info(f"Results saved to {results_dir}")
        
        # Clean up
        await adapter.shutdown()
        
        return results_dir
        
    except Exception as e:
        logger.error(f"Error in research workflow: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

"""
## 9. Reproducibility Verification

To verify reproducibility, we can run the same experiment multiple times with the same seed.
"""

async def verify_reproducibility(num_runs: int = 2) -> bool:
    """Verify that the research workflow produces the same results with the same seed."""
    logger.info(f"Verifying reproducibility with {num_runs} runs")
    
    # Create a base configuration
    base_config = ExperimentConfig(seed=42)
    base_config.experiment_name = "reproducibility_verification"
    
    results_dirs = []
    analysis_files = []
    
    # Run the experiment multiple times
    for i in range(num_runs):
        logger.info(f"Starting run {i+1}/{num_runs}")
        
        # Create a copy of the configuration with a different timestamp
        config = ExperimentConfig(seed=base_config.seed)
        config.experiment_name = f"{base_config.experiment_name}_run{i+1}"
        
        # Run the workflow
        results_dir = await run_research_workflow(config)
        results_dirs.append(results_dir)
        
        # Store the analysis file path
        analysis_files.append(os.path.join(results_dir, "analysis.json"))
    
    # Compare analysis files
    analyses = []
    for file_path in analysis_files:
        with open(file_path, 'r') as f:
            analyses.append(json.load(f))
    
    # Check if all analyses are identical
    is_reproducible = True
    for i in range(1, len(analyses)):
        if analyses[i] != analyses[0]:
            logger.error(f"Run {i+1} produced different results from run 1")
            is_reproducible = False
    
    if is_reproducible:
        logger.info("Reproducibility verified: all runs produced identical results")
    else:
        logger.error("Reproducibility check failed: runs produced different results")
    
    return is_reproducible

"""
## Running the Demo

To run this research workflow example, execute the following code:
"""

if __name__ == "__main__":
    # Run the research workflow
    results_dir = asyncio.run(run_research_workflow())
    print(f"Results saved to {results_dir}")
    
    # Verify reproducibility (optional)
    # is_reproducible = asyncio.run(verify_reproducibility(num_runs=2))
    # print(f"Reproducibility verified: {is_reproducible}")

"""
## Conclusion

This notebook demonstrated a complete research workflow using Llama Stack, focusing on:

1. **Explicit Configuration**: All parameters are documented and saved
2. **Reproducibility**: Fixed random seeds ensure consistent results
3. **Comprehensive Logging**: Detailed logging of all operations
4. **Data Persistence**: All experiment data is saved for future reference
5. **Results Analysis**: Automated analysis and visualization of results
6. **Verification**: Reproducibility can be explicitly verified

By following these practices, researchers can ensure their work is transparent,
reproducible, and maintainable, facilitating collaboration across disciplines.
"""
