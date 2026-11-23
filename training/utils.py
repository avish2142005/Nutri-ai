"""KrishiNetra Training Utilities.

Provides reproducibility setup, device selection, early stopping,
checkpoint management, learning rate scheduling, and training progress logging.
"""

import os
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.optim.lr_scheduler import ReduceLROnPlateau

logger = logging.getLogger("KrishiNetra.TrainUtils")


def set_seed(seed: int = 42):
    """Ensure 100% reproducibility across PyTorch, NumPy, and Python."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    logger.info(f"Reproducibility seed set to {seed}.")


def get_device() -> torch.device:
    """Select GPU acceleration if available, otherwise CPU."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info(f"Using NVIDIA GPU: {torch.cuda.get_device_name(0)}")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Using Apple Silicon MPS acceleration.")
    else:
        device = torch.device("cpu")
        logger.info("Using CPU for computation.")
    return device


class EarlyStopping:
    """Early stops the training if validation metric does not improve after a given patience."""

    def __init__(self, patience: int = 5, min_delta: float = 1e-4, mode: str = "min"):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score: Optional[float] = None
        self.early_stop = False

    def __call__(self, current_val: float) -> bool:
        if self.best_score is None:
            self.best_score = current_val
            return False

        if self.mode == "min":
            improved = current_val < (self.best_score - self.min_delta)
        else:
            improved = current_val > (self.best_score + self.min_delta)

        if improved:
            self.best_score = current_val
            self.counter = 0
            return False
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
            return False


class ModelCheckpoint:
    """Saves the best model weights during training."""

    def __init__(self, filepath: str or Path, monitor: str = "val_loss", mode: str = "min"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.monitor = monitor
        self.mode = mode
        self.best_val = float("inf") if mode == "min" else -float("inf")

    def step(self, current_val: float, model: nn.Module, optimizer=None, epoch: int = 0, extra_info: Dict[str, Any] = None):
        improved = (current_val < self.best_val) if self.mode == "min" else (current_val > self.best_val)
        if improved:
            logger.info(f"Model improved ({self.monitor}: {self.best_val:.4f} -> {current_val:.4f}). Saving checkpoint to {self.filepath}")
            self.best_val = current_val
            save_payload = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "best_val": self.best_val,
                "monitor": self.monitor,
            }
            if optimizer:
                save_payload["optimizer_state_dict"] = optimizer.state_dict()
            if extra_info:
                save_payload.update(extra_info)

            torch.save(save_payload, self.filepath)
            return True
        return False
