# dev-toolkit

A curated, code-first toolkit for mastering core software engineering concepts: data structures & algorithms, problem-solving patterns, system design, databases, and cloud fundamentals.

## Goals

- Build a single, well-structured reference for interviews and real-world problem solving.  
- Learn by reading clean code with step-by-step, debugger-style explanations.  
- Grow incrementally: start from basics, then layer in advanced variants and optimizations.

## Project Structure

- `AllAlgorithms/`  
  Fundamental algorithms grouped by category (searching, sorting, graphs, etc.) with clear complexity notes.

- `AllProblemSolvingPatterns/`  
  Reusable patterns like two pointers, sliding window, binary search on answer, prefix sums, and more.

- `README.md`  
  High-level overview and learning guidelines.

## Conventions

- Language: **Python 3.14+**.[web:10][web:15]  
- One concept per file, with:
  - A top comment block describing the idea, use cases, and a worked example.
  - Clean, type-annotated code with minimal but meaningful inline comments.
  - Time and space complexity notes.
- File naming:
  - Algorithms: `01_linear_search.py`, `02_binary_search.py`, etc.
  - Patterns: `01_two_pointers_basic.py`, `02_sliding_window_fixed.py`, etc.

## How to Use This Repo

1. Pick a topic (e.g., searching algorithms or two pointers pattern).  
2. Read the top comment block and walk through the example mentally (or in a debugger).  
3. Run the file, then modify the example input and predict the output before executing.  
4. Re-implement the idea from scratch in a separate scratchpad file without looking.

This project is designed to be extended continuously: add new files, keep the naming consistent, and prefer clarity over cleverness.
