#!/bin/sh
for q in Q2_K Q4_K_M Q8_0; do
  ./llama-bench -m qwen-$q.gguf -p 512 -n 128
done
