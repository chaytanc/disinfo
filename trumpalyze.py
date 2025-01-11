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
n_tweets = 1000
# Do not change the order of this array
narratives = ["America is too tolerant of foreigners and nontraditional behaviors", "America needs strong men to lead it", "Russia is an ally"]
# Set the display precision
pd.options.display.float_format = '{:.2f}'.format
np.set_printoptions(precision=2, suppress=True)

# class Result():
#     def __init__(self, tweet, similarities, sim_ind):
#         self.tweet = tweet
#         self.similarities = similarities # np array
#         self.max_sim = np.max(similarities)
#         self.sim_ind = sim_ind
#         #self.min_sim = min(similarities, key=lambda similarity: similarity[1])

#     def __repr__(self):
#         return f"Result(tweet='{self.tweet}', sims={self.similarities})\n"
    
#     def __eq__(self, other):
#         return self.tweet == other.tweet
    
#     # This sorting style implies we primarily care if *any* score is high, not just a particular one or all of them
#     def __lt__(self, other):
#         return self.max_sim < other.max_sim

# If you want to save some semblance of OOP but still have numpy, you can have results class instead of indiv results obj
# might still keep results obj and just have ind reference to where it's located in similarities...? that mihgt be useful later
class Results():
    def __init__(self, tweet_file, n_tweets, narratives):
        self.df = pd.read_csv(tweet_file, encoding='utf-8', encoding_errors='ignore')
        # self.similarities = np.empty((n_tweets, len(narratives)))
        # self.results = []
        self.results = pd.DataFrame(columns=["Tweet", "Similarities", "Index"])
        self.n_tweets = n_tweets
        self.narratives = narratives
        # This should really be called by the user but what good is the results class if it has none ?
        self.get_results()

    # TODO -- leave model a global?
    def embed_narratives(self, narratives):
        nar_embeds = []
        for narrative in narratives:
            nar_embeds.append(model.encode(narrative, convert_to_tensor=True))
        return nar_embeds

    def get_results(self):
        nar_embeds = self.embed_narratives(self.narratives)
        # TODO could make df indexing parametrized or could just make unique analysis funcs (probably cleaner, though less modular)
        for i, tweet in enumerate(self.df["Tweet"][:self.n_tweets]):
            embedding= model.encode(tweet, convert_to_tensor=True)
            tweet_sims = np.empty(len(nar_embeds))
            for j, nar_embed in enumerate(nar_embeds):
                sim = util.pytorch_cos_sim(embedding, nar_embed)
                tweet_sims[j] = sim
            # self.similarities[i] = tweet_sims
            # self.results.append(Result(tweet, tweet_sims, i))
            self.results.loc[i] = {"Tweet" : tweet, "Similarities": tweet_sims, "Index" : i} # TODO Store index for later?

    def __repr__(self):
        return f"First 10 Results: \n {self.results[:10]}"

# Show results with highest similarity ratings in any narrative dimension
results = Results(file, n_tweets, narratives)
print(results)
print(results.results["Similarities"])
sorted_results = results.results.sort_values(by="Similarities", key=lambda col: col.apply(np.max))
print("Lowest sims: ", sorted_results[:10])
print("Highest sims: ", sorted_results[-10:])

# What if I want a function that takes in a particular narrative and sorts based on the highest in that category
# TODO use similarities matrix
def sort_by_narrative(narrative_ind, results):
    narrative_sims = results.results["Similarities"].apply(lambda sim_array: sim_array[narrative_ind])
    print(narrative_sims.sort_values())
    return sorted(narrative_sims)

# Use an LLM summary to generate possible narratives
# https://huggingface.co/Ayush-1722/Meta-Llama-3-8B-Instruct-Summarize-v0.2-16K-LoRANET-Merged
# see chatgpt logs for prototyping
# https://chatgpt.com/c/6779fbe0-4960-800d-afe2-f5902b41de77

# Compare RT article to WSJ article on same topic wrt generated possible russia narratives or expert narratives
# eventually use actual disinfo database as baseline

# Go paragraph by paragraph in article and add up similarity score?

# TODO is there a way to inject geopolitical context into comparison? dates & headlines?
