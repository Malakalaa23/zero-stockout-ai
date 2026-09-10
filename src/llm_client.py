import os
import time
from typing import Optional


# List of models to try in order
FALLBACK_MODELS = [
    "meta-llama/Llama-3.2-3B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3-mini-4k-instruct",
    "HuggingFaceH4/zephyr-7b-beta",
    "Qwen/Qwen2.5-7B-Instruct",
]


class HuggingFaceLLM:
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        use_api: bool = True,
    ):
        self.use_api = use_api
        self.client = None
        self.model_name = None

        if use_api:
            try:
                from huggingface_hub import InferenceClient
            except ImportError as exc:
                raise RuntimeError(
                    "Install huggingface_hub: pip install huggingface_hub"
                ) from exc

            api_key = api_key or os.getenv("HF_API_KEY") or os.getenv("HUGGINGFACE_API_KEY")
            if not api_key:
                raise ValueError("HF_API_KEY not set in environment")

            # Build list of models to try
            models_to_try = []
            if model_name:
                models_to_try.append(model_name)
            models_to_try.extend([m for m in FALLBACK_MODELS if m != model_name])

            # Try each model with retries because provider startup requests can be transient.
            for model in models_to_try:
                for attempt in range(3):
                    try:
                        client = InferenceClient(
                            model=model,
                            provider=os.getenv("HF_PROVIDER", "auto"),
                            token=api_key,
                        )
                        client.chat_completion(
                            messages=[{"role": "user", "content": "hi"}],
                            max_tokens=5,
                        )
                        self.client = client
                        self.model_name = model
                        print(f"Using model: {model}")
                        break
                    except Exception as e:
                        if attempt == 2:
                            print(f"Model {model} failed: {str(e)[:120]}")
                        else:
                            time.sleep(1)
                if self.client is not None:
                    break

            if self.client is None:
                raise RuntimeError("All models failed. Try again later.")

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        if self.use_api:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()

        # Local mode (not used here)
        raise RuntimeError("Local mode not implemented")


class MockLLM:
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        marker = "QUESTION:" if "QUESTION:" in prompt else "USER QUESTION:"
        if marker in prompt:
            q = prompt.split(marker, 1)[1].split("ANSWER:", 1)[0].strip()
            return f"[Mock LLM] Answer for: {q}"
        return "[Mock LLM] No question found."