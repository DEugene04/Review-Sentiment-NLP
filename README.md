# Review Sentiment NLP

A full-stack project that analyzes customer reviews and extracts insights using Natural Language Processing.

## Project Structure

review-nlp/
--backend/#FastAPI backend
--frontend/#React + Vite dashboard

## Features

- Upload and analyze customer reviews
- Sentiment analysis using NLP
- Topic extraction
- Interactive dashboard visualization

## Tech Stack

**Frontend**

- React
- Vite
- TypeScript
- TailwindCSS
- ShadCN UI

**Backend**

- FastAPI
- Python
- PostgreSQL

**NLP**

- Python NLP libraries
- Machine learning models for sentiment analysis

## Setup

### Prerequisites

Node.js (v20.19+)

### Terminal 1

cd backend
uvicorn main:app --reload --port 8000

### Terminal 2

cd frontend
npm install
npm run dev
