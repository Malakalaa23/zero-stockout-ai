import os
from typing import Optional


class HuggingFaceLLM:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
        api_key: Optional[str] = None,
        use_api: bool = True,
    ):
        self.model_name = model_name
        self.use_api = use_api
        self.client = None
        self.pipeline = None

        if use_api:
            try:
                from huggingface_hub import InferenceClient
            except ImportError as exc:
                raise RuntimeError("Install huggingface_hub: pip install huggingface_hub") from exc

            api_key = api_key or os.getenv("HF_API_KEY") or os.getenv("HUGGINGFACE_API_KEY")
            if not api_key:
                raise ValueError("HF_API_KEY not set in environment")

            self.client = InferenceClient(
                model=model_name,
                provider=os.getenv("HF_PROVIDER", "auto"),
                token=api_key,
            )
        else:
            try:
                from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
                import torch
            except ImportError as exc:
                raise RuntimeError("Install transformers torch: pip install transformers torch") from exc

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
            )
            self.pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=400,
                temperature=0.3,
                do_sample=True,
            )

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        if self.use_api:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()

        result = self.pipeline(prompt)
        text = result[0]["generated_text"]
        if text.startswith(prompt):
            text = text[len(prompt):]
        return text.strip()


class MockLLM:
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        if "السؤال:" in prompt:
            q = prompt.split("السؤال:")[1].split("الإجابة")[0].strip()
            return f"[Mock LLM] إجابة على: {q}"
        return "[Mock LLM] No question found."