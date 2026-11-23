"""
Script to train the KrishiNetra BPE tokenizer on the agricultural domain corpus.
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from llm.config import LLMConfig
from llm.tokenizer.bpe_tokenizer import BPETokenizer

def train_and_save_tokenizer():
    config = LLMConfig()
    corpus_path = config.corpus_path
    
    if not os.path.exists(corpus_path):
        raise FileNotFoundError(f"Corpus file not found at {corpus_path}. Run build_corpus.py first.")

    with open(corpus_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into lines/paragraphs for training
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    print(f"Loaded {len(paragraphs)} paragraphs from {corpus_path}.")

    tokenizer = BPETokenizer()
    print(f"Training BPE Tokenizer up to vocab size {config.vocab_size}...")
    tokenizer.train(paragraphs, target_vocab_size=config.vocab_size)

    save_dir = config.tokenizer_dir
    tokenizer.save(save_dir)
    print(f"Saved trained tokenizer to {save_dir}")

    # Test tokenization
    test_text = "Early blight in tomato is caused by Alternaria solani."
    encoded = tokenizer.encode(test_text)
    decoded = tokenizer.decode(encoded)
    print(f"Test sentence: '{test_text}'")
    print(f"Encoded tokens ({len(encoded)}): {encoded}")
    print(f"Decoded text: '{decoded}'")
    assert decoded.strip() == test_text.strip(), f"Decoded mismatch: '{decoded}' vs '{test_text}'"
    print("Tokenizer verification successful!")

if __name__ == "__main__":
    train_and_save_tokenizer()
