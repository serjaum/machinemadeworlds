X (141 chars):
KV cache: the reused memory of past tokens that decides how many sessions fit per GPU: https://machinemadeworlds.com/posts/glossary-kv-cache/

LinkedIn (58 words):
Long chats slow down when the model recomputes the past each token. The KV cache fixes that.

This glossary entry explains the KV cache in plain terms — stored attention keys and values that trade GPU memory for speed, why agent workloads multiply the cost, how quantization shrinks it, and which context settings matter in vLLM, llama.cpp, and Ollama.

https://machinemadeworlds.com/posts/glossary-kv-cache/

RSS (71 chars):
KV cache, plainly: reused past-token memory that caps sessions per GPU.
