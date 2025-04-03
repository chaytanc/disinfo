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
# from langchain_core.exceptions import OutputParserException
# from langchain.output_parsers import OutputFixingParser
# from langchain_openai import ChatOpenAI
# from langchain_ollama import ChatOllama
import json
import re
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
        
        # Try loading the file, handle errors gracefully
        try:
            self.df = pd.read_csv(file, encoding="utf-8", encoding_errors="ignore")
        except FileNotFoundError:
            raise ValueError(f"Error: The file '{file}' was not found.")
        except pd.errors.EmptyDataError:
            raise ValueError(f"Error: The file '{file}' is empty or corrupted.")
        except Exception as e:
            raise ValueError(f"Error loading file '{file}': {e}")
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

    def generate_narratives(self, progress=None):
        # Set up a parser + inject instructions into the prompt template.
        parser = JsonOutputParser(pydantic_object=self.NarrativeSummary)
        llm = MLXPipeline(model=self.summary_model, tokenizer=self.tokenizer, pipeline_kwargs={"response_format" :
          {"type": "json_object",}})
        prompt = self.create_format_prompt(parser)
        chain = prompt | llm | self.parse_json_objects 

        # What happens when we have way more than 300 tweets? Can we still cluster 50,000 or do we chunk it by time and regen narratives?
        clustered_tweets = self.cluster_embedded_tweets(self.df["Tweet"])
        responses = []
        if progress != None:
            for chunk in progress.tqdm(clustered_tweets):
                # resp, prompt = process_chunk(chunk, self.summary_model, self.tokenizer)
                resp = chain.invoke({"query": chunk})
                # TODO remove print
                print(resp)
                if not resp:
                    continue
                responses.append(resp[0])
        else:
            for chunk in (clustered_tweets):
                resp = chain.invoke({"query": chunk})
                if not resp:
                    continue
                responses.append(resp[0])
 
        return responses, prompt, clustered_tweets

    def format(self, raw_narratives):
        # Formats to markdown for direct display as a string.
        formatted_output = ""
        # Loop through the outer list (each narrative set)
        for idx, narrative_set in enumerate(raw_narratives, 1):
            if not narrative_set:  # Skip empty lists
                continue

            formatted_output += f"### Narrative Set {idx}\n"

            # Loop through each narrative (which is a dictionary)
            for key, value in narrative_set.items():
                formatted_output += f"- **{key.replace('_', ' ').capitalize()}**: {value}\n"

            formatted_output += "\n---\n\n"

        return formatted_output.strip()


    def get_html_formatted_outputs(self, raw_narratives):
        outputs = []
        for idx, narrative_set in enumerate(raw_narratives, 1):
            if not narrative_set:  # Skip empty lists
                continue
            
            # Start a container div for each narrative pair
            formatted_output = f"<div class='narrative-block' data-narrative-id='{idx}'>"
            formatted_output += "<hr class='narrative-separator'>" 

            for key, value in narrative_set.items():
                formatted_output += f"""
                <div class='narrative-item'>
                    <strong>{key.replace('_', ' ').capitalize()}:</strong>
                    <p>{value}</p>
                </div>
                """

            formatted_output += "</div>"  # Close block div
            outputs.append(formatted_output)

        return outputs


    def save_json_narratives(self, json_list):
        # Save JSON for download
        json_file = "generated_narratives.json"
        with open(json_file, "w") as f:
            json.dump(json_list, f, indent=4)
        return json_file


    def parse_json_objects(self, text):
        """
        Identifies JSON objects between curly braces and attempts to parse them.
        Returns a list of successfully parsed JSON objects.
        Raises an error if parsing any JSON object fails, but continues processing others.
        """
        # Regex to find JSON objects between curly braces {}
        json_objects = re.findall(r'\{.*?\}', text, re.DOTALL)
        
        parsed_json_list = []  # To store successfully parsed JSON objects

        # Loop through each potential JSON object
        for json_str in json_objects:
            try:
                # Try parsing the JSON string
                parsed_json = json.loads(json_str)
                parsed_json_list.append(parsed_json)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}. Skipping invalid JSON object.")
                continue  # Skip the invalid JSON and continue processing other objects

        return parsed_json_list


    # def parse_narratives(self, raw_narratives):
    #     """
    #     Parses a list of JSON strings into Python dictionaries
    #     and returns a formatted markdown string + a downloadable JSON file.
    #     """
    #     formatted_output = ""
    #     json_list = []

    #     for i, json_str in enumerate(raw_narratives, 1):
    #         try:
    #             narrative_obj = json.loads(json_str)  # Convert JSON string to dict
    #             json_list.append(narrative_obj)

    #             formatted_output += f"### Narrative Set {i}\n"
    #             for key, value in narrative_obj.items():
    #                 formatted_output += f"- **{key.replace('_', ' ').capitalize()}**: {value}\n"
    #             formatted_output += "\n---\n\n"
    #         except json.JSONDecodeError:
    #             formatted_output += f"⚠️ Error parsing narrative {i}: {json_str}\n\n"

    #     # Save JSON for download
    #     json_file = "generated_narratives.json"
    #     with open(json_file, "w") as f:
    #         json.dump(json_list, f, indent=4)

    #     return formatted_output.strip(), json_file
    
    # Define your desired data structure.
    class NarrativeSummary(BaseModel):
        narrative_1: str = Field(description="Most dominant narrative")
        narrative_2: str = Field(description="Second dominant narrative")

# For tweet in timeline of tweets, sim score to each of X number of generated narratives, and add to list
    # Plot each list of similarities to narrative over time

#TODO LLM Validation: 
    # Have people randomly sample tweets from the batches and agree or disagree with the top 2 narratives presented (and write in alternative if desired)
#TODO Similarity validation
    # Given valid narratives, have people code tweets as belonging to or not belonging to those
# TODO filter out retweets / response tweets? Adjust prompt to account for this? For example, respondign to fake news CNN tweets criticizing his policies are confusing the LLM
