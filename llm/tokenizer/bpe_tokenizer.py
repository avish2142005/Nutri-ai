"""
Byte Pair Encoding (BPE) Subword Tokenizer built from scratch in pure Python.
No external tokenizer libraries or APIs required.
Includes special token handling, vocabulary saving/loading, and fast greedy pair merging.
"""
import json
import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple


class BPETokenizer:
    def __init__(self, special_tokens: Optional[List[str]] = None):
        self.special_tokens = special_tokens or [
            "<|pad|>",
            "<|unk|>",
            "<|bos|>",
            "<|eos|>",
            "<|im_start|>",
            "<|im_end|>",
        ]
        self.merges: List[Tuple[str, str]] = []
        self.merge_ranks: Dict[Tuple[str, str], int] = {}
        self.token_to_id: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self.space_prefix = "Ġ"  # Representation for leading whitespace

        # Initialize special tokens
        for idx, token in enumerate(self.special_tokens):
            self.token_to_id[token] = idx
            self.id_to_token[idx] = token

    @property
    def pad_token_id(self) -> int:
        return self.token_to_id["<|pad|>"]

    @property
    def unk_token_id(self) -> int:
        return self.token_to_id["<|unk|>"]

    @property
    def bos_token_id(self) -> int:
        return self.token_to_id["<|bos|>"]

    @property
    def eos_token_id(self) -> int:
        return self.token_to_id["<|eos|>"]

    @property
    def vocab_size(self) -> int:
        return len(self.token_to_id)

    def _pre_tokenize(self, text: str) -> List[List[str]]:
        """
        Split text into words while preserving spaces with space_prefix.
        Returns a list of character lists for each word.
        """
        # Split on whitespace while keeping whitespace information
        tokens = re.findall(r"\w+|[^\w\s]|\s+", text)
        word_splits = []
        for tok in tokens:
            if not tok:
                continue
            if tok.isspace():
                # Encode spaces as prefix
                word_splits.append([self.space_prefix])
            else:
                word_splits.append(list(tok))
        return word_splits

    def train(self, texts: List[str], target_vocab_size: int = 1000):
        """
        Train BPE merges on input corpus until target_vocab_size is reached.
        """
        # 1. Collect all initial characters
        words_freq = Counter()
        for text in texts:
            words = re.findall(r"\w+|[^\w\s]|\s+", text)
            for w in words:
                if not w:
                    continue
                if w.isspace():
                    words_freq[(self.space_prefix,)] += 1
                else:
                    words_freq[tuple(w)] += 1

        # 2. Add all unique base characters to vocab
        base_chars = set()
        for word_tuple in words_freq.keys():
            for ch in word_tuple:
                base_chars.add(ch)

        current_id = len(self.token_to_id)
        for ch in sorted(base_chars):
            if ch not in self.token_to_id:
                self.token_to_id[ch] = current_id
                self.id_to_token[current_id] = ch
                current_id += 1

        # 3. Iteratively merge most frequent pair
        num_merges = max(0, target_vocab_size - len(self.token_to_id))
        self.merges = []
        self.merge_ranks = {}

        for merge_idx in range(num_merges):
            pair_counts = Counter()
            for word_tuple, freq in words_freq.items():
                if len(word_tuple) < 2:
                    continue
                for i in range(len(word_tuple) - 1):
                    pair = (word_tuple[i], word_tuple[i + 1])
                    pair_counts[pair] += freq

            if not pair_counts:
                break

            # Best pair
            best_pair, best_freq = pair_counts.most_common(1)[0]
            if best_freq < 2:
                break  # Stop if pair frequency is negligible

            # Register merge
            merged_token = best_pair[0] + best_pair[1]
            self.merges.append(best_pair)
            self.merge_ranks[best_pair] = merge_idx

            if merged_token not in self.token_to_id:
                self.token_to_id[merged_token] = current_id
                self.id_to_token[current_id] = merged_token
                current_id += 1

            # Update words_freq
            new_words_freq = Counter()
            for word_tuple, freq in words_freq.items():
                new_word = []
                i = 0
                while i < len(word_tuple):
                    if (
                        i < len(word_tuple) - 1
                        and word_tuple[i] == best_pair[0]
                        and word_tuple[i + 1] == best_pair[1]
                    ):
                        new_word.append(merged_token)
                        i += 2
                    else:
                        new_word.append(word_tuple[i])
                        i += 1
                new_words_freq[tuple(new_word)] += freq
            words_freq = new_words_freq

        print(
            f"BPE Tokenizer trained: {len(self.token_to_id)} tokens, {len(self.merges)} merges."
        )

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        """
        Tokenize a text string into a list of token IDs.
        """
        if not text:
            return []

        # Check for special tokens in text and preserve them
        pattern = "|".join(re.escape(tok) for tok in self.special_tokens)
        segments = []
        last_end = 0
        for match in re.finditer(pattern, text):
            start, end = match.span()
            if start > last_end:
                segments.append((text[last_end:start], False))
            segments.append((match.group(0), True))
            last_end = end
        if last_end < len(text):
            segments.append((text[last_end:], False))

        token_ids = []
        if add_special_tokens:
            token_ids.append(self.bos_token_id)

        for content, is_special in segments:
            if is_special:
                token_ids.append(self.token_to_id.get(content, self.unk_token_id))
            else:
                words = re.findall(r"\w+|[^\w\s]|\s+", content)
                for w in words:
                    if not w:
                        continue
                    if w.isspace():
                        token_ids.append(
                            self.token_to_id.get(self.space_prefix, self.unk_token_id)
                        )
                    else:
                        symbols = list(w)
                        # Apply merges iteratively in rank order
                        while len(symbols) >= 2:
                            pairs = [
                                (symbols[i], symbols[i + 1])
                                for i in range(len(symbols) - 1)
                            ]
                            # Find pair with lowest rank
                            valid_pairs = [
                                (self.merge_ranks[p], p)
                                for p in pairs
                                if p in self.merge_ranks
                            ]
                            if not valid_pairs:
                                break
                            valid_pairs.sort()
                            best_pair = valid_pairs[0][1]

                            # Merge all occurrences of best_pair in symbols
                            new_symbols = []
                            i = 0
                            while i < len(symbols):
                                if (
                                    i < len(symbols) - 1
                                    and symbols[i] == best_pair[0]
                                    and symbols[i + 1] == best_pair[1]
                                ):
                                    new_symbols.append(best_pair[0] + best_pair[1])
                                    i += 2
                                else:
                                    new_symbols.append(symbols[i])
                                    i += 1
                            symbols = new_symbols

                        for s in symbols:
                            token_ids.append(self.token_to_id.get(s, self.unk_token_id))

        if add_special_tokens:
            token_ids.append(self.eos_token_id)

        return token_ids

    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Convert token IDs back into string text.
        """
        tokens = []
        for tid in token_ids:
            if tid not in self.id_to_token:
                continue
            tok = self.id_to_token[tid]
            if skip_special_tokens and tok in self.special_tokens:
                continue
            tokens.append(tok)

        text = "".join(tokens)
        # Restore space prefix
        text = text.replace(self.space_prefix, " ")
        return text

    def save(self, directory: str):
        """Save vocabulary and merge rules to directory."""
        os.makedirs(directory, exist_ok=True)
        vocab_data = {
            "token_to_id": self.token_to_id,
            "special_tokens": self.special_tokens,
            "merges": [list(m) for m in self.merges],
        }
        with open(
            os.path.join(directory, "tokenizer_config.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(vocab_data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, directory: str) -> "BPETokenizer":
        """Load tokenizer from directory."""
        path = os.path.join(directory, "tokenizer_config.json")
        with open(path, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        tokenizer = cls(special_tokens=vocab_data.get("special_tokens"))
        tokenizer.token_to_id = vocab_data["token_to_id"]
        tokenizer.id_to_token = {int(v): k for k, v in tokenizer.token_to_id.items()}
        tokenizer.merges = [tuple(m) for m in vocab_data["merges"]]
        tokenizer.merge_ranks = {
            tuple(m): idx for idx, m in enumerate(tokenizer.merges)
        }
        return tokenizer
