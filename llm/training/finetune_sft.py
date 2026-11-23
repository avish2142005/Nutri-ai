"""
Stage 4: Supervised Fine-Tuning (SFT) for KrishiNetra LLM.
Fine-tunes the pretrained base model on agricultural prompt-response instruction pairs:
<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n{response}<|im_end|>
"""
import math
import os
import sys
import time
import json
import torch
from torch.utils.data import DataLoader, random_split

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from llm.config import LLMConfig
from llm.tokenizer.bpe_tokenizer import BPETokenizer
from llm.data.dataset import SFTDataset
from llm.model.transformer import KrishiNetraLM


def run_sft_finetuning():
    config = LLMConfig()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- KrishiNetra LLM Instruction Fine-Tuning (SFT) Starting on Device: {device} ---")

    # 1. Load Tokenizer
    tokenizer = BPETokenizer.load(config.tokenizer_dir)

    # 2. Instantiate Model and Load Pretrained Base Weights
    model = KrishiNetraLM(config).to(device)
    if os.path.exists(config.base_model_path):
        print(f"Loading pretrained base checkpoint from {config.base_model_path}...")
        checkpoint = torch.load(config.base_model_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        print(f"Base checkpoint loaded! Base Val Loss was: {checkpoint.get('val_loss', 'N/A')}")
    else:
        print("Pretrained base checkpoint not found. Training from scratch directly.")

    # 3. Load SFT Instruction Dataset
    sft_dataset = SFTDataset(config.sft_data_path, tokenizer, block_size=config.block_size)
    print(f"Loaded {len(sft_dataset)} instruction samples from {config.sft_data_path}")

    val_size = max(1, int(len(sft_dataset) * 0.15))
    train_size = len(sft_dataset) - val_size
    train_dataset, val_dataset = random_split(
        sft_dataset, [train_size, val_size], generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)

    # 4. SFT Optimizer (Conservative learning rate for fine-tuning)
    sft_lr = 1.5e-4
    optimizer = torch.optim.AdamW(model.parameters(), lr=sft_lr, weight_decay=0.01)

    # 5. Fine-Tuning Loop
    sft_iters = 180
    eval_interval = 30
    best_val_loss = float("inf")
    history = {"step": [], "train_loss": [], "val_loss": [], "perplexity": []}

    train_iter = iter(train_loader)
    start_time = time.time()

    model.train()
    for step in range(sft_iters):
        try:
            x, y = next(train_iter)
        except StopIteration:
            train_iter = iter(train_loader)
            x, y = next(train_iter)

        x, y = x.to(device), y.to(device)

        optimizer.zero_grad()
        _, loss = model(x, y)
        loss.backward()

        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step % eval_interval == 0 or step == sft_iters - 1:
            model.eval()
            val_losses = []
            with torch.no_grad():
                for vx, vy in val_loader:
                    vx, vy = vx.to(device), vy.to(device)
                    _, vloss = model(vx, vy)
                    val_losses.append(vloss.item())
            val_loss = sum(val_losses) / max(len(val_losses), 1)
            ppl = math.exp(min(val_loss, 20.0))
            elapsed = time.time() - start_time

            print(
                f"SFT Step {step:3d}/{sft_iters} | Train Loss: {loss.item():.4f} | Val Loss: {val_loss:.4f} | Perplexity: {ppl:.2f} | Elapsed: {elapsed:.1f}s"
            )

            history["step"].append(step)
            history["train_loss"].append(round(loss.item(), 4))
            history["val_loss"].append(round(val_loss, 4))
            history["perplexity"].append(round(ppl, 2))

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                sft_checkpoint = {
                    "model_state_dict": model.state_dict(),
                    "config": config.__dict__,
                    "step": step,
                    "val_loss": val_loss,
                    "perplexity": ppl,
                }
                torch.save(sft_checkpoint, config.sft_model_path)
                print(f"  --> Saved new best SFT model to {config.sft_model_path}")
            model.train()

    # Save SFT history
    history_path = os.path.join(config.weights_dir, "sft_history.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    total_time = time.time() - start_time
    print(f"\nSFT Instruction Fine-Tuning Completed in {total_time:.1f} seconds! Best Val Loss: {best_val_loss:.4f}")
    return model, tokenizer


if __name__ == "__main__":
    run_sft_finetuning()
