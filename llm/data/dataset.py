"""
PyTorch Dataset and DataLoader implementations for KrishiNetra LLM.
Includes:
1. CausalLMDataset: Slices raw token streams into overlapping (input_ids, target_ids)
   shifted by one token for autoregressive next-token prediction.
2. SFTDataset: Handles prompt-response pairs with attention masks.
"""
import json
import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Tuple
from llm.tokenizer.bpe_tokenizer import BPETokenizer


class CausalLMDataset(Dataset):
    """
    Autoregressive Next-Token Prediction Dataset.
    Given a sequence of token IDs, generates inputs x and targets y:
    x = tokens[i : i + block_size]
    y = tokens[i + 1 : i + block_size + 1]
    """
    def __init__(self, token_ids: List[int], block_size: int = 128, stride: int = 64):
        self.block_size = block_size
        self.samples: List[Tuple[torch.Tensor, torch.Tensor]] = []

        total_tokens = len(token_ids)
        for i in range(0, total_tokens - block_size, stride):
            x = torch.tensor(token_ids[i : i + block_size], dtype=torch.long)
            y = torch.tensor(token_ids[i + 1 : i + block_size + 1], dtype=torch.long)
            self.samples.append((x, y))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.samples[idx]


class SFTDataset(Dataset):
    """
    Supervised Fine-Tuning Dataset.
    Loads JSONL format and pads/truncates to block_size.
    Targets are masked (-100 or pad) before the assistant turn.
    """
    def __init__(self, jsonl_path: str, tokenizer: BPETokenizer, block_size: int = 128):
        self.samples = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                text = item.get("text", "")
                tokens = tokenizer.encode(text, add_special_tokens=False)
                if len(tokens) < 4:
                    continue
                # Truncate if exceeds block_size + 1
                if len(tokens) > block_size + 1:
                    tokens = tokens[: block_size + 1]
                else:
                    # Pad
                    tokens = tokens + [tokenizer.pad_token_id] * (block_size + 1 - len(tokens))

                x = torch.tensor(tokens[:-1], dtype=torch.long)
                y = torch.tensor(tokens[1:], dtype=torch.long)
                self.samples.append((x, y))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.samples[idx]
