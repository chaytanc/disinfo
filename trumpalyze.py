# Get sentence similarity library
# Manually create some hypothesized trump narratives
# For each trump tweet, get similarity score to that narrative (100, say)
# look at how well it did, maybe cluster results based on similarities to different narratives, then examine those tweets?

from sentence_transformers import SentenceTransformer, util
import pandas as pd
import numpy as np

# TODO params file yaml
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
file = "trumptweets1205-127.csv"
# file = "syria_articles/wsj_article.txt"
n_tweets = 1000
# Do not change the order of this array
# State Dept. Narratives
narratives = ["Russia is an Innocent Victim", "The Collapse of Western Civilization is Imminent", "Popular Movements are U.S.-sponsored Color Revolutions",]
# Set the display precision
pd.options.display.float_format = '{:.2f}'.format
np.set_printoptions(precision=2, suppress=True)

class Results():
    def __init__(self, tweet_file, n_tweets, narratives):
        self.read_media(tweet_file)
        if n_tweets > len(self.df):
            n_tweets = len(self.df)
            print("Number of tweets selected is greater than total.\
                  \nContinuing with {num} tweets total.".format(num=n_tweets))
        self.n_tweets = n_tweets
        self.similarities = np.empty((self.n_tweets, len(narratives)))
        self.tweets = pd.DataFrame(columns=["Tweet", "Sim_Index"])
        self.narratives = narratives
        # This should really be called by the user but what good is the results class if it has none ?
        self.get_results()

    def read_media(self, file):
        if file.endswith(".csv"):
            self.df = pd.read_csv(file, encoding='utf-8', encoding_errors='ignore')
        elif file.endswith(".txt"):
            with open(file, "r") as f:
                content = f.read()
                self.df = pd.DataFrame({"Tweet": [content]})
            
    # TODO -- leave model a global?
    def embed_narratives(self, narratives):
        nar_embeds = []
        for narrative in narratives:
            nar_embeds.append(model.encode(narrative, convert_to_tensor=True))
        return nar_embeds

    def get_results(self):
        nar_embeds = self.embed_narratives(self.narratives)
        for i, tweet in enumerate(self.df["Tweet"][:self.n_tweets]):
            embedding = model.encode(tweet, convert_to_tensor=True)
            tweet_sims = np.empty(len(nar_embeds))
            for j, nar_embed in enumerate(nar_embeds):
                sim = util.pytorch_cos_sim(embedding, nar_embed)
                tweet_sims[j] = sim
            self.similarities[i] = tweet_sims
            self.tweets.loc[i] = {"Tweet" : tweet, "Sim_Index" : i}

    def sort_by_narrative(self, narrative_ind):
        if narrative_ind > len(self.narratives) - 1:
            print("Invalid narrative index. Continuing with narrative_ind=0...")
            narrative_ind = 0
        # Grab the column of the narrative_ind
        narr_sims = self.similarities.T[narrative_ind] # after we transpose, we have 3 rows and n_tweets cols
        sorted_args = np.argsort(narr_sims)
        # get the sorted sims and the sorted tweets
        sorted_sims = narr_sims[sorted_args]
        sorted_tweets = self.tweets.iloc[sorted_args]
        return sorted_tweets, sorted_sims

    def print_top_k(self, k, narrative_ind):
        if k > self.n_tweets:
            k = self.n_tweets
        if narrative_ind > len(self.narratives) - 1:
            print("Invalid narrative index. Continuing with narrative_ind=0...")
            narrative_ind = 0
        sorted_tweets, sorted_sims = self.sort_by_narrative(narrative_ind)
        sorted_tweets["Sims"] = sorted_sims
        pd.set_option('display.max_colwidth', None)
        print("{k} Most similar tweets to narrative \n\"{narrative}\": \n".format(
            k=k, narrative=self.narratives[narrative_ind]), 
            sorted_tweets[-k:])

    def __repr__(self):
        return f"First 10 Results: \n {self.tweets[:10]}"

# Show results with highest similarity ratings in any narrative dimension
results = Results(file, n_tweets, narratives)
print(results)
#sort_by_narrative(0, results)
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