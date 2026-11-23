"""
KrishiNetra LLM Service - Offline Agricultural Language Model Inference.
Loads the trained Decoder-Only Transformer (KrishiNetraLM) and custom BPE Tokenizer.
Generates grounded agronomic responses with ZERO external API calls or sensitive information.
"""
import os
import sys
import logging
import torch
from typing import Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from llm.config import LLMConfig
from llm.tokenizer.bpe_tokenizer import BPETokenizer
from llm.model.transformer import KrishiNetraLM
from llm.model.generation import generate_text

logger = logging.getLogger(__name__)


class KrishiNetraLLMService:
    _instance: Optional["KrishiNetraLLMService"] = None

    def __init__(self):
        self.config = LLMConfig()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer: Optional[BPETokenizer] = None
        self.model: Optional[KrishiNetraLM] = None
        self._load_model()

    @classmethod
    def get_instance(cls) -> "KrishiNetraLLMService":
        if cls._instance is None:
            cls._instance = KrishiNetraLLMService()
        return cls._instance

    def _load_model(self):
        try:
            tokenizer_dir = self.config.tokenizer_dir
            if not os.path.exists(os.path.join(tokenizer_dir, "tokenizer_config.json")):
                logger.warning("Tokenizer not found at %s", tokenizer_dir)
                return

            self.tokenizer = BPETokenizer.load(tokenizer_dir)
            self.model = KrishiNetraLM(self.config).to(self.device)

            model_path = (
                self.config.sft_model_path
                if os.path.exists(self.config.sft_model_path)
                else self.config.base_model_path
            )

            if os.path.exists(model_path):
                ckpt = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(ckpt["model_state_dict"])
                self.model.eval()
                logger.info("KrishiNetraLM successfully loaded from %s onto %s", model_path, self.device)
            else:
                logger.warning("LLM model weights not found at %s", model_path)
        except Exception as e:
            logger.error("Failed to load KrishiNetraLLM: %s", e)

    def is_available(self) -> bool:
        return self.model is not None and self.tokenizer is not None

    def answer_query(
        self,
        query: str,
        context: str = "",
        max_new_tokens: int = 120,
        temperature: float = 0.6,
        top_k: int = 35,
    ) -> str:
        """
        Generate an agricultural consultation response.
        """
        if not self.is_available():
            return "KrishiNetra LLM engine is currently initializing."

        full_prompt = f"<|im_start|>user\n{query}"
        if context:
            full_prompt += f" (Context: {context})"
        full_prompt += "<|im_end|>\n<|im_start|>assistant\n"

        try:
            raw_gen = generate_text(
                self.model,
                self.tokenizer,
                full_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                device=self.device,
            )

            # Extract assistant turn
            if "<|im_start|>assistant\n" in raw_gen:
                ans = raw_gen.split("<|im_start|>assistant\n")[-1]
            else:
                ans = raw_gen

            ans = ans.replace("<|im_end|>", "").replace("<|eos|>", "").strip()
            return ans
        except Exception as err:
            logger.error("Error in KrishiNetraLM text generation: %s", err)
            return "Unable to complete text generation at this moment."
