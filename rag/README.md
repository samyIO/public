# RAG Systems

Functional, but work in progress

## Introduction

In this project you can find different RAG Systems that you can use to explore the other projects.
These are just simple implementations that should give some ideas when approaching RAG Systems

## Available Systems

1. **Qdrant RAG**: Simple Qdrant implementation with UI, that uses a majority filter method and displays information about the retrieval steps in the UI.

2. **LightRAG**: Chat-like implementation of lightRAG, a framework that seems to be a promising approach.

## Usage

### Prerequisits

- running ollama endpoint
- downloaded model 'llama3.1:8b' and 'nomic-embed-text'
- running qdrant endpoint (please refer to the [documentation](https://qdrant.tech/documentation/quickstart/))

### Linux

### Create & activate a virtual environment

```bash
python3 -m venv venv
```
```bash
source venv/bin/activate
```
### Install the dependencies

```bash
pip install -r requirements.txt
```
### Run the program

```bash
streamlit run src/qdrant.py (or lightRAG.py)
```

### Windows

### Create & activate a virtual environment

```cmd
python -m venv venv
```
```cmd
venv\Scripts\activate
```
### Install the dependencies

```cmd
pip install -r requirements.txt
```
### Run the program

```cmd
streamlit run src/qdrant.py (or lightRAG.py)
```