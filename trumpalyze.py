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
from preprocess import read_media

# Set the display precision
pd.options.display.float_format = '{:.2f}'.format
np.set_printoptions(precision=2, suppress=True)

# RQ: Can we show that set X had Y% similarity to Z narrative, which 
# TODO params file yaml
file = "tweets/trumptweets1205-127.csv"
summary_model, tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
sent_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# file = "syria_articles/wsj_article.txt"
max_tweets = 100000
num_narratives = 3
# Do not change the order of this array
# State Dept. Narratives
narratives = ["Russia is an Innocent Victim", "The Collapse of Western Civilization is Imminent", "Popular Movements are U.S.-sponsored Color Revolutions",]
def run_narrative_generation(file):
    generator = Narrative_Generator(summary_model, tokenizer, sent_model, file, num_narratives)
    trump_nars, _, _ = generator.generate_narratives()
    formatted = generator.format(trump_nars)
    return formatted

print(run_narrative_generation(file))
# Show results with highest similarity ratings in any narrative dimension
df = read_media(file)
results = Results(sent_model, df, max_tweets, narratives)
results.print_top_k(k=10, narrative_ind=0)

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