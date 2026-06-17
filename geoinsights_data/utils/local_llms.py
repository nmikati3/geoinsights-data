import os
from pathlib import Path

from llama_cpp import Llama

_hf_cache = os.environ.get(
    "HF_HOME",
    str(Path(__file__).resolve().parents[2] / ".cache" / "huggingface"),
)
os.makedirs(_hf_cache, exist_ok=True)
os.environ.setdefault("HF_HOME", _hf_cache)
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", _hf_cache)

_REPO_ID = "unsloth/gemma-4-E4B-it-GGUF"
_FILENAME = "gemma-4-E4B-it-Q4_K_M.gguf"

_CLIENT_LLAMA = None


def _get_client() -> Llama:
    global _CLIENT_LLAMA
    if _CLIENT_LLAMA is None:
        llama_kwargs = {
            "n_ctx": int(os.environ.get("LLAMA_N_CTX", "32768")),
            "verbose": False,
        }
        model_path = os.environ.get("LLAMA_MODEL_PATH")
        if model_path:
            _CLIENT_LLAMA = Llama(model_path=model_path, **llama_kwargs)
        else:
            _CLIENT_LLAMA = Llama.from_pretrained(
                repo_id=_REPO_ID,
                filename=_FILENAME,
                **llama_kwargs,
            )
    return _CLIENT_LLAMA


def get_labels_local_llm(content, system_prompt):

    response = _get_client().create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        max_tokens=8192,
        response_format={"type": "json_object"},
    )

    return response["choices"][0]["message"]["content"]
