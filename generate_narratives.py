import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from mlx_lm import load, generate
from sentence_transformers import SentenceTransformer, util

model, tokenizer = load("mlx-community/Llama-3.2-3B-Instruct-4bit")
sent_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# Recursion prompt
#sys_prompt = "You should find the dominant narratives in the following batches of tweets, or synthesize the dominant narratives from the presented summaries. Do not simply summarize each list given (if given a list of narratives instead of raw tweets), but instead find the commonalities between the different lists given and summarize the most dominant narratives from there:\n"
# Simple prompt
sys_prompt = "You should find the top two dominant narratives in the following batch of tweets. Do not cite which tweets correspond to the narratives, just supply the narrative summaries "
file = "trumptweets1205-127.csv"

smallest_batch_size = 10
num_narratives = 8

def preprocess_context_window(file):
    if file.endswith(".txt"):
        with open(file, "r") as f:
            # batch tweets together somehow -- append previously found narratives to the new batch of tweets? Largest batch possible? very small frequent chunks? Enough to get a general sense of thoughts? Very small then aggregate up multiple times?
            pass #TODO
    elif file.endswith(".csv"):
        df = pd.read_csv(file, encoding='utf-8', encoding_errors='ignore')
        # Create n_tweets / smallest_batch_size chunks of tweets / data
        chunks = chunk_it(df, smallest_batch_size)
        return chunks

def chunk_it(array, k):
    return np.array_split(array, np.ceil(len(array) / k).astype(int))

def create_prompt(tokenizer, sys_prompt, user_prompt):
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    prompt = tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
    )
    return prompt

def cluster_embedded_tweets(tweets):
    embeddings = []
    for tweet in tweets:
        embeddings.append(sent_model.encode(tweet, convert_to_numpy=True))
    clusters = KMeans(n_clusters=num_narratives).fit(embeddings)
    unique_labels = np.unique(clusters.labels_)
    # Chunk tweets by cluster labels
    clustered_tweets = [tweets[clusters.labels_ == label] for label in unique_labels]
    return clustered_tweets

# TODO yaml
def process_chunk(chunk, model, tokenizer):
    prompt = create_prompt(tokenizer, sys_prompt, user_prompt=chunk)
    response = generate(
        model, tokenizer, 
        #temperature=0.9, top_p=0.8, 
        max_tokens=512, prompt=prompt, 
        verbose=True)
    return response, prompt

# all_chunks = preprocess_context_window(file)
# chunks = all_chunks.copy()
# for chunk in chunks:
#     outputs, prompt = process_chunk(chunk, model, tokenizer)
#     print(outputs[0]["generated_text\n"][len(prompt):])

def merge(chunks):
    print("CHUNK LEN :D", len(chunks))
    if len(chunks) == 1:
        return chunks

    new_chunks = [] 
    for chunk in chunks:
        resp, _ = process_chunk(chunk, model, tokenizer)
        new_chunks.append(resp)
    new_chunks = chunk_it(new_chunks, smallest_batch_size)
    chunks = merge(new_chunks)

# all_chunks = preprocess_context_window(file)
# chunks = merge(all_chunks)
# print(chunks)

df = pd.read_csv(file, encoding='utf-8', encoding_errors='ignore')
clustered_tweets = cluster_embedded_tweets(df["Tweet"])
for chunk in clustered_tweets:
    print(chunk.shape)
    resp, _ = process_chunk(chunk, model, tokenizer)



#TODO LLM Validation: 
    # Have people randomly sample tweets from the batches and agree or disagree with the top 2 narratives presented (and write in alternative if desired)

# TODO filter out retweets / response tweets? Adjust prompt to account for this? For example, respondign to fake news CNN tweets criticizing his policies are confusing the LLM
