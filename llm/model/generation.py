"""
Autoregressive Text Generation Engine for KrishiNetra LLM.
Supports:
- Temperature scaling
- Top-k filtering
- Top-p (nucleus) filtering
- Repetition penalty
- Stop tokens (<|im_end|>, <|eos|>)
"""
import torch
import torch.nn.functional as F
from typing import List, Optional
from llm.model.transformer import KrishiNetraLM
from llm.tokenizer.bpe_tokenizer import BPETokenizer


@torch.no_grad()
def generate_text(
    model: KrishiNetraLM,
    tokenizer: BPETokenizer,
    prompt: str,
    max_new_tokens: int = 100,
    temperature: float = 0.7,
    top_k: int = 40,
    top_p: float = 0.9,
    repetition_penalty: float = 1.15,
    stop_tokens: Optional[List[int]] = None,
    device: str = "cpu",
) -> str:
    """
    Generate text from a prompt string using the trained KrishiNetraLM model.
    """
    model.eval()
    if stop_tokens is None:
        stop_tokens = [tokenizer.eos_token_id]
        if "<|im_end|>" in tokenizer.token_to_id:
            stop_tokens.append(tokenizer.token_to_id["<|im_end|>"])

    # Tokenize prompt
    input_ids = tokenizer.encode(prompt, add_special_tokens=False)
    if not input_ids:
        input_ids = [tokenizer.bos_token_id]

    idx = torch.tensor(input_ids, dtype=torch.long, device=device).unsqueeze(0)

    for _ in range(max_new_tokens):
        # Crop context if sequence exceeds block size
        idx_cond = idx if idx.size(1) <= model.config.block_size else idx[:, -model.config.block_size :]

        # Forward the model to get the logits for the index in the sequence
        logits, _ = model(idx_cond)
        # Pluck the logits at the final step
        logits = logits[:, -1, :]

        # Apply repetition penalty
        if repetition_penalty != 1.0:
            for token_id in set(idx[0].tolist()):
                if logits[0, token_id] < 0:
                    logits[0, token_id] *= repetition_penalty
                else:
                    logits[0, token_id] /= repetition_penalty

        # Temperature scaling
        if temperature > 0:
            logits = logits / temperature

            # Top-k filtering
            if top_k > 0:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = -float("Inf")

            # Top-p (nucleus) filtering
            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                sorted_indices_to_remove = cumulative_probs > top_p
                # Shift the indices to the right to keep also the first token above the threshold
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = 0
                indices_to_remove = sorted_indices[sorted_indices_to_remove]
                logits[:, indices_to_remove] = -float("Inf")

            # Sample from the filtered distribution
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
        else:
            # Greedy argmax
            next_token = torch.argmax(logits, dim=-1, keepdim=True)

        token_id = next_token.item()

        # Check for stop tokens
        if token_id in stop_tokens:
            break

        # Append next token to sequence
        idx = torch.cat((idx, next_token), dim=1)

    # Decode generated tokens
    output_ids = idx[0].tolist()
    generated_text = tokenizer.decode(output_ids)
    return generated_text
