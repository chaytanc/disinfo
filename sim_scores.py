import pandas as pd
import numpy as np
from sentence_transformers import util

class Results():
    def __init__(self, model, tweet_file, n_tweets, narratives):
        self.model = model
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
            
    def embed_narratives(self, narratives):
        nar_embeds = []
        for narrative in narratives:
            nar_embeds.append(self.model.encode(narrative, convert_to_tensor=True))
        return nar_embeds

    def get_results(self):
        nar_embeds = self.embed_narratives(self.narratives)
        for i, tweet in enumerate(self.df["Tweet"][:self.n_tweets]):
            embedding = self.model.encode(tweet, convert_to_tensor=True)
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