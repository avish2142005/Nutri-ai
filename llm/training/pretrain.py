"""
Stage 3: Pretraining Pipeline for KrishiNetra LLM from scratch.
Implements:
1. Autoregressive next-token prediction
2. Cosine learning rate scheduling with warmup
3. AdamW optimizer with decoupled weight decay
4. Gradient clipping & Perplexity tracking
5. Model checkpointing
"""
import math
import os
import sys
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from llm.config import LLMConfig
from llm.tokenizer.bpe_tokenizer import BPETokenizer
from llm.data.dataset import CausalLMDataset
from llm.model.transformer import KrishiNetraLM


def get_lr(it: int, config: LLMConfig) -> float:
    # 1) Linear warmup for warmup_iters steps
    if it < config.warmup_iters:
        return config.learning_rate * it / config.warmup_iters
    # 2) If it > lr_decay_iters, return min learning rate
    if it > config.lr_decay_iters:
        return config.min_learning_rate
    # 3) In between, use cosine decay down to min learning rate
    decay_ratio = (it - config.warmup_iters) / (config.lr_decay_iters - config.warmup_iters)
    assert 0 <= decay_ratio <= 1
    coeff = 0.5 * (1.0 + math.cos(math.pi * decay_ratio))  # coeff ranges 0 to 1
    return config.min_learning_rate + coeff * (config.learning_rate - config.min_learning_rate)


@torch.no_grad()
def estimate_loss(model: KrishiNetraLM, dataloader: DataLoader, device: str, max_batches: int = 10) -> float:
    model.eval()
    losses = []
    for idx, (x, y) in enumerate(dataloader):
        if idx >= max_batches:
            break
        x, y = x.to(device), y.to(device)
        _, loss = model(x, y)
        losses.append(loss.item())
    model.train()
    return float(sum(losses) / max(len(losses), 1))


def run_pretraining():
    config = LLMConfig()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- KrishiNetra LLM Pretraining Starting on Device: {device} ---")

    # 1. Load Tokenizer
    tokenizer = BPETokenizer.load(config.tokenizer_dir)
    print(f"Loaded tokenizer with vocabulary size: {tokenizer.vocab_size}")

    # 2. Load Raw Corpus
    with open(config.corpus_path, "r", encoding="utf-8") as f:
        corpus_text = f.read()

    # Encode entire corpus into tokens
    print(f"Encoding pretraining corpus ({len(corpus_text)} chars)...")
    all_tokens = tokenizer.encode(corpus_text, add_special_tokens=True)
    print(f"Total tokens in corpus: {len(all_tokens):,}")

    # 3. Create Dataset and Train/Val split
    dataset = CausalLMDataset(all_tokens, block_size=config.block_size, stride=32)
    val_size = max(1, int(len(dataset) * 0.15))
    train_size = len(dataset) - val_size
    train_dataset, val_dataset = random_split(
        dataset, [train_size, val_size], generator=torch.Generator().manual_seed(42)
    )
    print(f"Dataset samples: {len(dataset)} total | {train_size} train | {val_size} validation")

    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=False)

    # 4. Instantiate Model
    model = KrishiNetraLM(config).to(device)
    print(f"KrishiNetraLM Model Initialized: {model.get_num_params():,} parameters.")

    # 5. Optimizer (AdamW with decoupled weight decay on non-1D parameters)
    param_dict = {pn: p for pn, p in model.named_parameters() if p.requires_grad}
    decay_params = [p for n, p in param_dict.items() if p.dim() >= 2]
    nodecay_params = [p for n, p in param_dict.items() if p.dim() < 2]
    optim_groups = [
        {"params": decay_params, "weight_decay": config.weight_decay},
        {"params": nodecay_params, "weight_decay": 0.0},
    ]
    optimizer = torch.optim.AdamW(optim_groups, lr=config.learning_rate, betas=(0.9, 0.95))

    # 6. Training Loop
    os.makedirs(config.weights_dir, exist_ok=True)
    best_val_loss = float("inf")
    history = {"train_loss": [], "val_loss": [], "perplexity": [], "step": []}

    train_iter = iter(train_loader)
    start_time = time.time()

    for step in range(config.max_iters):
        # Determine and set learning rate
        lr = get_lr(step, config)
        for param_group in optimizer.param_groups:
            param_group["lr"] = lr

        # Get next batch
        try:
            x, y = next(train_iter)
        except StopIteration:
            train_iter = iter(train_loader)
            x, y = next(train_iter)

        x, y = x.to(device), y.to(device)

        # Forward pass
        optimizer.zero_grad(set_to_none=True)
        _, loss = model(x, y)
        loss.backward()

        # Gradient clipping
        if config.grad_clip != 0.0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip)

        optimizer.step()

        # Periodic Evaluation
        if step % config.eval_interval == 0 or step == config.max_iters - 1:
            val_loss = estimate_loss(model, val_loader, device, max_batches=config.eval_iters)
            ppl = math.exp(min(val_loss, 20.0))  # Safeguard against overflow
            elapsed = time.time() - start_time

            print(
                f"Step {step:4d}/{config.max_iters} | Train Loss: {loss.item():.4f} | Val Loss: {val_loss:.4f} | Perplexity: {ppl:.2f} | LR: {lr:.2e} | Elapsed: {elapsed:.1f}s"
            )

            history["step"].append(step)
            history["train_loss"].append(round(loss.item(), 4))
            history["val_loss"].append(round(val_loss, 4))
            history["perplexity"].append(round(ppl, 2))

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                checkpoint = {
                    "model_state_dict": model.state_dict(),
                    "config": config.__dict__,
                    "step": step,
                    "val_loss": val_loss,
                    "perplexity": ppl,
                }
                torch.save(checkpoint, config.base_model_path)
                print(f"  --> Saved new best base model to {config.base_model_path}")

    # Save training history
    history_path = os.path.join(config.weights_dir, "pretrain_history.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    total_time = time.time() - start_time
    print(f"\nPretraining Completed in {total_time:.1f} seconds! Best Val Loss: {best_val_loss:.4f}")
    return model, tokenizer


if __name__ == "__main__":
    run_pretraining()
