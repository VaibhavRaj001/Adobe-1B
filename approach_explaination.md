# Approach Explanation: Persona-Driven Document Intelligence

## Introduction

The goal of this project was to create an intelligent system that analyzes a collection of PDF documents and extracts the most relevant information based on a specific user **persona** and their **job-to-be-done**. The core challenge lies in understanding the user's intent semantically and pinpointing relevant content within unstructured documents, all while operating under strict offline, CPU-only constraints.

Our solution employs a robust two-stage pipeline that combines reliable content processing with state-of-the-art semantic search.

## Stage 1: Reliable Paragraph Chunking

Initial exploration revealed that rule-based structural parsing (i.e., heading detection based on font size or style) is brittle and fails on documents with non-standard formatting. To ensure reliability across any document set, we pivoted to a more resilient **paragraph-based chunking** strategy.

This method processes each PDF and segments the text based on natural paragraph breaks (typically double newlines). This approach is highly effective because:
1.  **It's Universal:** It doesn't depend on inconsistent visual formatting.
2.  **It Creates Coherent Units:** Paragraphs are naturally self-contained, semantically-focused units, making them ideal for analysis.

This provides a clean and reliable foundation for the next stage without making risky assumptions.

## Stage 2: Persona-Driven Semantic Search

Once the documents are broken down into paragraph chunks, the core intelligence layer takes over.

1.  **Dynamic Query Formulation:** The user's `persona` and `job_to_be_done` are combined into a single, descriptive query string (e.g., "As a Travel Planner, I need to plan a trip...").

2.  **Vector Embeddings:** We use a highly efficient, pre-trained language model (`all-MiniLM-L6-v2` from the `sentence-transformers` library). This model converts both the dynamic query and all paragraph chunks into numerical representations (vectors) that capture their underlying meaning.

3.  **Similarity Ranking:** Using **cosine similarity**, we calculate the semantic "distance" between the query vector and every chunk vector. The chunks with the highest similarity scores are ranked as the most relevant, directly generating the required `importance_rank`.

## Output Generation

For the final JSON output:
-   **`section_title`**: Since we no longer detect formal headings, a pragmatic title is generated using the first ~75 characters of the top-ranked paragraph itself.
-   **`subsection_analysis`**: To provide a more granular answer, we perform a "micro-search" within each top-ranked paragraph to extract the single sentence that is most semantically similar to the user's query.

This entire pipeline is lightweight, deterministic, and fully self-contained within the Docker image, successfully meeting all performance and operational constraints of the hackathon.

---

## 🐳 Docker Instructions

---

### 🏗️ Step 1: Build the Docker Image

docker build -t persona-intel .

### 🏗️ Step 2: Run the Docker Image

#### 🔹 For Linux/macOS (bash):
docker run --rm -v "$(pwd):/app" persona-intel


#### 🔹 For Windows CMD:
docker run --rm -v %cd%:/app persona-intel


#### 🔹 Windows PowerShell:
docker run --rm -v ${PWD}:/app persona-intel
