import transformers
from transformers import AutoModelForCausalLM
import pandas as pd
import numpy as np

from unsloth import FastLanguageModel
import torch
import os

token = os.environ.get("HFTOKEN")
model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = True
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Meta-Llama-3.1-8B",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
    token = token,
)
FastLanguageModel.for_inference(model)

sys_prompt = "You should find the narratives in the following batches of tweets"
file = "trumptweets1205-127.csv"

# TODO starting with just tweets
smallest_batch_size = 10

def preprocess_context_window(file):
    if file.endswith(".txt"):
        with open(file, "r") as f:
            # batch tweets together somehow -- append previously found narratives to the new batch of tweets? Largest batch possible? very small frequent chunks? Enough to get a general sense of thoughts? Very small then aggregate up multiple times?
            pass #TODO
    elif file.endswith(".csv"):
        df = pd.read_csv(file)
        # Create n_tweets / smallest_batch_size chunks of tweets / data
        chunks = np.array_split(df, np.ceil(len(df) / smallest_batch_size).astype(int))
    return chunks

# TODO yaml
def config_model(model_id):
    pipeline = transformers.pipeline(
        "text-generation",
        model=model,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="auto",
    )
    terminators = [
        pipeline.tokenizer.eos_token_id,
        pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]
    return pipeline, terminators

def create_prompt(pipeline, sys_prompt, user_prompt):
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    prompt = pipeline.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
    )
    return prompt

def process_chunk(chunk, pipeline, terminators):
    prompt = create_prompt(pipeline, sys_prompt, user_prompt=chunk)
    outputs = pipeline(
        prompt,
        max_new_tokens=256,
        eos_token_id=terminators,
        do_sample=True,
        temperature=0.6,
        top_p=0.9,
    )
    return outputs, prompt

pipeline, terminators = config_model(model_id)
chunks = preprocess_context_window(file)
for chunk in chunks:
    outputs, prompt = process_chunk(chunk, pipeline, terminators)
    print(outputs[0]["generated_text\n"][len(prompt):])
