nohup python main.py \
    --save_path output/core_set_py1.jsonl \
    --input_path 'TheStack_V2/repo_meta/Python/Python_src_1.jsonl' \
    --batch_size 1024 \
    --seed 42 \
    --model_name sentence-transformers/all-roberta-large-v1 \
    --coreset_size 4691  > output/output1.log 2>&1 &