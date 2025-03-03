import pandas as pd
import numpy as np
from mlx_lm import generate
from sklearn.cluster import KMeans
# from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFacePipeline
from langchain_community.llms.mlx_pipeline import MLXPipeline
from langchain_core.exceptions import OutputParserException
from langchain.output_parsers import OutputFixingParser
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()
# Simple prompt
SYS_PROMPT = "You should find the top two dominant narratives in the following batch of tweets. Do not cite which tweets correspond to the narratives, just supply the narrative summaries. You must always return valid JSON fenced by a markdown code block. Do not return any additional text. "
# OUTPUT_PARSE_PROMPT = "Structure your response as a JSON object with {'narrative 1': value, 'narrative 2', value}"

smallest_batch_size = 10

class Narrative_Generator():
    def __init__(self, summary_model, tokenizer, embedding_model, file, num_narratives):
        self.summary_model = summary_model
        self.tokenizer = tokenizer
        self.embedding_model = embedding_model
        self.num_narratives = num_narratives
        self.df = pd.read_csv(file, encoding='utf-8', encoding_errors='ignore')
        # You could use preprocess_context_window here instead if data is too big...

    def preprocess_context_window(self, file):
        if file.endswith(".txt"):
            with open(file, "r") as f:
                #TODO batch tweets together somehow -- append previously found narratives to the new batch of tweets? Largest batch possible? very small frequent chunks? Enough to get a general sense of thoughts? Very small then aggregate up multiple times?
                pass
        elif file.endswith(".csv"):
            df = pd.read_csv(file, encoding='utf-8', encoding_errors='ignore')
            # Create n_tweets / smallest_batch_size chunks of tweets / data
            chunks = self.chunk_it(df, smallest_batch_size)
            return chunks

    def chunk_it(self, array, k):
        return np.array_split(array, np.ceil(len(array) / k).astype(int))

    def create_prompt(self, tokenizer, user_prompt):
        messages = [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        
        prompt = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
        )
        return prompt

    def create_format_prompt(self, parser):
        prompt = PromptTemplate(
            template= SYS_PROMPT+"\n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        return prompt

    def cluster_embedded_tweets(self, tweets):
        embeddings = []
        for tweet in tweets:
            # TODO this is NOT clustering the embeddings, it's clustering the fucking input ids
            # Why does it seem to work then? TODO visualize the spread of these clusters and the tweets within the clusters
            # Lowkey this can be done later -- having bugs like this that affect the outcome but not the look of the prototype can be addressed later
            # Wait lowkey this might work bc it's the info retrieval semantic sim model, have to check docs on the output of encode
            embeddings.append(self.embedding_model.encode(tweet, convert_to_numpy=True))
        clusters = KMeans(n_clusters=self.num_narratives).fit(embeddings)
        unique_labels = np.unique(clusters.labels_)
        # Chunk tweets by cluster labels
        clustered_tweets = [tweets[clusters.labels_ == label] for label in unique_labels]
        return clustered_tweets

    # TODO yaml
    # TODO private functions
    def process_chunk(self, chunk, model, tokenizer):
        prompt = self.create_prompt(tokenizer, SYS_PROMPT, user_prompt=chunk)
        response = generate(
            model, tokenizer, 
            #temperature=0.9, top_p=0.8, 
            max_tokens=512, prompt=prompt, 
            verbose=True)
        return response, prompt

    def generate_narratives(self):
        # Set up a parser + inject instructions into the prompt template.
        parser = JsonOutputParser(pydantic_object=self.NarrativeSummary)
        # pipe = pipeline("summarization", model=self.summary_model, tokenizer=self.tokenizer, temperature=0.1)
        # llm = HuggingFacePipeline(pipeline=pipe)
        # llm = MLXPipeline(model=self.summary_model, tokenizer=self.tokenizer, pipeline_kwargs={"temp": 0.1})
        # llm = MLXPipeline(model=self.summary_model, tokenizer=self.tokenizer, pipeline_kwargs={"max_tokens": 50, "temp": None})
        llm = MLXPipeline(model=self.summary_model, tokenizer=self.tokenizer)
        prompt = self.create_format_prompt(parser)
        chain = prompt | llm | parser
        chain = prompt | llm

        # What happens when we have way more than 300 tweets? Can we still cluster 50,000 or do we chunk it by time and regen narratives?
        clustered_tweets = self.cluster_embedded_tweets(self.df["Tweet"])
        for chunk in clustered_tweets:
            # resp, prompt = process_chunk(chunk, self.summary_model, self.tokenizer)
            resp = chain.invoke({"query": chunk})
            try:
                parser.parse(resp)
            except OutputParserException as e:
                print(e)
                new_parser = OutputFixingParser.from_llm(parser=parser, llm=ChatOllama(model="deepseek-r1",
    temperature=0.8, num_predict=256))
                new_parser.parse(resp)
        return resp, prompt
    
    # Define your desired data structure.
    class NarrativeSummary(BaseModel):
        narrative1: str = Field(description="Most dominant narrative")
        narrative2: str = Field(description="Second dominant narrative")

# For tweet in timeline of tweets, sim score to each of X number of generated narratives, and add to list
    # Plot each list of similarities to narrative over time

#TODO LLM Validation: 
    # Have people randomly sample tweets from the batches and agree or disagree with the top 2 narratives presented (and write in alternative if desired)
#TODO Similarity validation
    # Given valid narratives, have people code tweets as belonging to or not belonging to those
# TODO filter out retweets / response tweets? Adjust prompt to account for this? For example, respondign to fake news CNN tweets criticizing his policies are confusing the LLM
