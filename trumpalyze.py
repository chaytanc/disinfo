# Get sentence similarity library
# Manually create some hypothesized trump narratives
# For each trump tweet, get similarity score to that narrative (100, say)
# look at how well it did, maybe cluster results based on similarities to different narratives, then examine those tweets?

from sentence_transformers import SentenceTransformer, util
import pandas as pd
import numpy as np
from mlx_lm import load 
from sim_scores import Results
from generate_narratives import Narrative_Generator

# Set the display precision
pd.options.display.float_format = '{:.2f}'.format
np.set_printoptions(precision=2, suppress=True)

# RQ: Can we show that set X had Y% similarity to Z narrative, which 
# TODO params file yaml
file = "trumptweets1205-127.csv"
summary_model, tokenizer = load("mlx-community/Llama-3.2-3B-Instruct-4bit")
sent_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# file = "syria_articles/wsj_article.txt"
max_tweets = 1000
num_narratives = 8
# Do not change the order of this array
# State Dept. Narratives
narratives = ["Russia is an Innocent Victim", "The Collapse of Western Civilization is Imminent", "Popular Movements are U.S.-sponsored Color Revolutions",]
trump_nars, _ = Narrative_Generator(summary_model, tokenizer, sent_model, file, num_narratives).generate_narratives()

# Show results with highest similarity ratings in any narrative dimension
results = Results(file, max_tweets, narratives)
results.print_top_k(k=10, narrative_ind=3)

# Use an LLM summary to generate possible narratives
# https://huggingface.co/Ayush-1722/Meta-Llama-3-8B-Instruct-Summarize-v0.2-16K-LoRANET-Merged
# see chatgpt logs for prototyping
# https://chatgpt.com/c/6779fbe0-4960-800d-afe2-f5902b41de77

# Compare RT article to WSJ article on same topic wrt generated possible russia narratives or expert narratives
# eventually use actual disinfo database as baseline
# TODO replicate findings of some paper

# Go paragraph by paragraph in article and add up similarity score?

# TODO is there a way to inject geopolitical context into comparison? dates & headlines?

# TODO more data https://www.thetrumparchive.com/?resultssortOption=%22Latest%22

# Pipeline: embed tweets, cluster, generate narratives, get similarity score of embedded tweets to narratives
    # seems redundant but is actually useful for getting de novo narratives and confirming what experts already get

#TODO semantic similarity of gatewaypundit tweets to trump tweets over time?
# Where might the transgender military idea come from???