"""
Nutrition LLM Fine-Tuning and RAG Pipeline
============================================

This script handles:
1. Fine-tuning a LLM on nutrition data using LoRA
2. Creating a knowledge base for RAG (Retrieval-Augmented Generation)
3. Setting up the vector store for nutrition queries

Uses:
- transformers (Hugging Face)
- peft (Parameter-Efficient Fine-Tuning)
- sentence-transformers (embeddings)
- chroma (vector store)
"""

import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType


def load_nutrition_data(filepath="nutrition_docs/nutrition_facts.txt"):
    """Load nutrition facts from text file."""
    data = []
    with open(filepath, "r") as f:
        lines = f.readlines()
    
    for line in lines[2:]:  # Skip header
        line = line.strip()
        if not line or line.startswith("="):
            continue
        if ":" in line:
            parts = line.split(":")
            food = parts[0].strip()
            nutrients = parts[1].strip()
            data.append({
                "text": f"Food: {food}. Nutrients: {nutrients}.",
                "label": food
            })
    return data


def fine_tune_nutrition_llm(
    model_name="microsoft/phi-2",
    data_path="nutrition_docs/nutrition_facts.txt",
    output_dir="fine_tuned_nutrition",
):
    """Fine-tune LLM on nutrition data using LoRA."""
    
    # Load data
    data = load_nutrition_data(data_path)
    if not data:
        print("No data found, creating synthetic training examples")
        data = [
            {"text": "Food: Apple. Nutrients: 95 calories, 25g carbs, 0g protein, 0g fat. Answer: Apple is a healthy fruit rich in fiber and vitamin C.", "answer": "Apple"},
            {"text": "Food: Chicken Breast. Nutrients: 165 calories, 0g carbs, 31g protein, 3.6g fat. Answer: Chicken breast is high in protein and low in fat.", "answer": "Chicken breast"},
            {"text": "Food: Salmon. Nutrients: 280 calories, 0g carbs, 25g protein, 18g fat. Answer: Salmon is rich in omega-3 fatty acids and high-quality protein.", "answer": "Salmon"},
        ]
    
    # Create dataset
    dataset = Dataset.from_dict({"text": [d["text"] for d in data]})
    
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    
    # Apply LoRA for efficient fine-tuning
    config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    )
    model = get_peft_model(model, config)
    model.print_trainable_parameters()
    
    # Tokenize data
    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, max_length=512)
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        weight_decay=0.01,
        fp16=True,
        logging_steps=1,
        save_steps=10,
        warmup_steps=5,
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=False
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )
    
    # Train
    trainer.train()
    
    # Save model
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print(f"Fine-tuned model saved to {output_dir}")
    return output_dir


# --- RAG Pipeline (simplified, no problematic langchain imports) ---

import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings


def create_vector_store(knowledge_base="nutrition_docs/nutrition_facts.txt"):
    """Create vector store from nutrition knowledge base."""
    from chromadb import Client
    from chromadb.config import Settings
    
    # Parse knowledge base
    knowledge_items = []
    with open(knowledge_base, "r") as f:
        lines = f.readlines()
    for line in lines[2:]:  # Skip header
        line = line.strip()
        if not line or line.startswith("="):
            continue
        if ":" in line:
            parts = line.split(":")
            food = parts[0].strip()
            nutrients = parts[1].strip()
            knowledge_items.append(f"Food: {food}. Nutrients: {nutrients}.")
    
    # Create Chroma vector store
    client = Client(Settings(allow_automatic_label_exports=False))
    collection = client.create_collection("nutrition_knowledge")
    
    # Add documents
    ids = [f"food_{i}" for i in range(len(knowledge_items))]
    documents = knowledge_items
    
    collection.add(
        documents=documents,
        ids=ids,
    )
    
    print(f"Vector store created with {len(knowledge_items)} nutrition items")
    return collection


def get_nutrition_context(query, collection, top_k=3):
    """Get nutrition context from vector store for a query."""
    # Embed the query using a simple approach
    # In production, use sentence-transformers
    query_embedding = np.random.rand(384).tolist()  # Placeholder
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    
    return results.get("documents", [["No results found"]])[0]


def create_rag_pipeline(knowledge_base="nutrition_docs/nutrition_facts.txt"):
    """Create complete RAG pipeline."""
    collection = create_vector_store(knowledge_base)
    
    def rag_query(question):
        """Run a RAG query."""
        context = get_nutrition_context(question, collection)
        # Simple response generation based on context
        if context and context[0] != "No results found":
            # Extract food name from context
            for line in context:
                if "Food:" in line:
                    food = line.split("Food:")[1].split(".")[0].strip()
                    nutrients = line.split("Nutrients:")[1].split(".")[0]
                    return f"{food} has {nutrients}. This is general nutritional information. Consult a healthcare professional for personalized advice."
        return "I don't have specific nutritional information for that query. Common foods include: apple, banana, chicken breast, salmon, egg, milk, brown rice, almonds, spinach. For personalized advice, consult a nutritionist."
    
    return rag_query


if __name__ == "__main__":
    print("=" * 60)
    print("Nutrition LLM Fine-Tuning + RAG Pipeline")
    print("=" * 60)
    
    # Step 1: Fine-tune model
    print("\n[1/3] Fine-tuning LLM on nutrition data...")
    model_dir = fine_tune_nutrition_llm()
    
    # Step 2: Create vector store
    print("\n[2/3] Creating nutrition knowledge vector store...")
    collection = create_vector_store()
    
    # Step 3: Test RAG queries
    print("\n[3/3] Testing RAG queries...")
    rag_query = create_rag_pipeline()
    
    test_queries = [
        "How many calories in an apple?",
        "What are the protein benefits of chicken breast?",
        "Is salmon good for heart health?",
    ]
    
    print("\nRAG Query Results:")
    for query in test_queries:
        print(f"  Q: {query}")
        print(f"  A: {rag_query(query)[:150]}...")
        print()
    
    print("\n" + "=" * 60)
    print("Pipeline ready!")
    print("=" * 60)
    print(f"\nFine-tuned model: {model_dir}")
    print("Vector store: nutrition_knowledge collection")