"""
Configuration module for KrishiNetra LLM architecture, training, and tokenization.
All parameters are customizable and optimized for high-efficiency training and CPU/GPU execution.
"""
import os
from dataclasses import dataclass, field
from typing import Optional

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@dataclass
class LLMConfig:
    # Model Architecture
    vocab_size: int = 1200          # Vocabulary size for domain BPE tokenizer
    block_size: int = 128           # Context window / maximum sequence length
    n_layer: int = 4                # Number of Transformer blocks
    n_head: int = 4                 # Number of attention heads
    n_embd: int = 256               # Embedding dimension (d_model)
    dropout: float = 0.1            # Dropout probability
    bias: bool = False              # Use bias in Linears and LayerNorms (like LLaMA/GPT-3)

    # Special Tokens
    pad_token: str = "<|pad|>"
    unk_token: str = "<|unk|>"
    bos_token: str = "<|bos|>"
    eos_token: str = "<|eos|>"
    im_start_token: str = "<|im_start|>"
    im_end_token: str = "<|im_end|>"

    # Training Hyperparameters
    batch_size: int = 16
    learning_rate: float = 6e-4
    min_learning_rate: float = 6e-5
    warmup_iters: int = 40
    lr_decay_iters: int = 300
    max_iters: int = 350
    weight_decay: float = 0.1
    grad_clip: float = 1.0
    eval_interval: int = 50
    eval_iters: int = 20

    # Paths (Absolute resolution anchored to KrishiNetra root)
    corpus_path: str = os.path.join(_ROOT_DIR, "llm", "data", "raw_corpus.txt")
    sft_data_path: str = os.path.join(_ROOT_DIR, "llm", "data", "sft_data.jsonl")
    tokenizer_dir: str = os.path.join(_ROOT_DIR, "llm", "weights", "tokenizer")
    weights_dir: str = os.path.join(_ROOT_DIR, "llm", "weights")
    base_model_path: str = os.path.join(_ROOT_DIR, "llm", "weights", "krishinetra_llm_base.pt")
    sft_model_path: str = os.path.join(_ROOT_DIR, "llm", "weights", "krishinetra_llm_sft.pt")
