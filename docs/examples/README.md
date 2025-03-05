# Llama Stack Example Notebooks

This directory contains example notebooks demonstrating how to use Llama Stack for reproducible research and high-quality code practices. These examples showcase best practices for ensuring reproducibility, robust error handling, and comprehensive documentation in research code.

## Examples

### 1. Reproducible Vector Search

[01_reproducible_vector_search.py](./01_reproducible_vector_search.py)

This example demonstrates how to use Llama Stack for reproducible vector search operations, ensuring consistent results across different runs and environments. Key topics covered:

- Setting random seeds for reproducibility
- Creating isolated random generators
- Vector database operations with SQLiteVec
- Verifying reproducibility by running the same query multiple times

### 2. Error Handling Best Practices

[02_error_handling_best_practices.py](./02_error_handling_best_practices.py)

This example showcases best practices for error handling in Llama Stack, focusing on robust type conversion, graceful failure, and comprehensive logging. Key topics covered:

- Robust type conversion for handling unexpected input types
- Graceful failure and recovery mechanisms
- Comprehensive logging for tracking operations and diagnosing issues
- Practical implementation in a robust vector database client

### 3. Research Workflow Example

[03_research_workflow_example.py](./03_research_workflow_example.py)

This example demonstrates a complete research workflow using Llama Stack, focusing on reproducibility, documentation, and best practices for research code. Key topics covered:

- Explicit configuration management
- Synthetic data generation with fixed seeds
- Vector database operations for document similarity
- Results analysis and visualization
- Data persistence for reproducibility
- Verification of reproducibility

## Usage

These examples can be run as Python scripts or converted to Jupyter notebooks for interactive exploration:

```bash
# Run as a Python script
python 01_reproducible_vector_search.py

# Convert to a Jupyter notebook
jupyter nbconvert --to notebook --execute 01_reproducible_vector_search.py
```

## Requirements

These examples require the following dependencies:

- Llama Stack
- NumPy
- Matplotlib (for visualization examples)
- Jupyter (for notebook conversion)

## Additional Resources

For more information on reproducibility and best practices in Llama Stack, see:

- [Reproducibility Documentation](../preprocessing/reproducibility_checklist.md)
- [Vector Database Operations](../preprocessing/vector_database_operations.md)
- [Embedding Generation](../preprocessing/embedding_generation.md)
- [Document Chunking](../preprocessing/document_chunking.md)
