import pandas as pd
from preprocess import read_media
from tqdm import tqdm

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_community.llms.mlx_pipeline import MLXPipeline
import re
import json
from mlx_lm import load 


# How many  w * retweets * similarity score
# Go through and reverse polarity based on sentiment analysis model

SYS_PROMPT = "You should evaluate if the following tweet is in support of, opposition to, or neutral to the following target narrative. If you are unsure you may mark that instead." 
class PolarityTester():
    def __init__(self, summary_model, tokenizer, data, target_narrative):
        self.summary_model = summary_model
        self.tokenizer = tokenizer
        self.df = data
        self.target_narrative = target_narrative

    def create_prompt(self, parser):
        prompt = PromptTemplate(
            template= SYS_PROMPT+"\n{format_instructions}\n\n Target narrative: {target_narrative}\n\n Tweet: {tweet}\n",
            input_variables=["target_narrative", "tweet"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        return prompt


    def create_response_object(self, responses):
        """ 
        Turn the one hot encoded positive, negative, neutral, unsure responses into a single response object 
        represented as a binary number 0-8 inclusive.
        """
        for i, resp in enumerate(responses):
            response_obj = ""
            for key, value in resp.items():
                response_obj += (str(value))
            resp['response_obj'] = int(response_obj, 2) # convert to base 2 binary literal for later checking polarity
            responses[i] = resp


    def parse_json_objects(self, text):
        """
        Identifies JSON objects between curly braces and attempts to parse them.
        Returns a list of successfully parsed JSON objects.
        Raises an error if parsing any JSON object fails, but continues processing others.
        Returns a list of one JSON object with keys 'narrative_1' and 'narrative_2'.
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
    

    def check_polarity(self):
        parser = JsonOutputParser(pydantic_object=self.TweetPolarity)
        llm = MLXPipeline(model=self.summary_model, tokenizer=self.tokenizer, pipeline_kwargs={
            "temp": 1.0,
          })
        prompt = self.create_prompt(parser)
        chain = prompt | llm | self.parse_json_objects 
        responses = []
        for tweet in tqdm(self.df['Tweet']):
            resp = chain.invoke({"target_narrative": self.target_narrative, "tweet": tweet})
            if not resp:
                continue
            responses.append(resp[0])

        self.create_response_object(responses)
        # Check that only only one polarity is marked as 1 and that the model is sure
        for i, resp in enumerate(responses):
            if resp['response_obj'] & 0b1000: # support
                resp['polarity'] = 'support'
            elif resp['response_obj'] & 0b0100: # opposition
                resp['polarity'] = 'opposition'
            elif resp['response_obj'] & 0b0010: # neutral
                resp['polarity'] = 'neutral'
            else:
                # TODO throw an error (or at least warning) if unsure?
                resp['polarity'] = 'unsure'
        response_df = pd.DataFrame(responses)
        self.df['polarity'] = response_df['polarity']

    
    def multiply_similarity_and_polarity(self):
        """
        Multiply the similarity score by the polarity score for each tweet.
        The polarity score is 1 for support, -1 for opposition, 1 for neutral, and 0 for unsure.
        Note that this 0s the similarity for unsure tweets.
        """
        polarity_map = {
            'support': 1,
            'opposition': -1,
            'neutral': 1,
            'unsure': 0
        }
        self.df['polarity_score'] = self.df['polarity'].map(polarity_map)
        self.df['similarity_score'] = self.df['Similarity'] * self.df['polarity_score']


    class TweetPolarity(BaseModel):
        postive : int = Field(description="A 1 indicating the tweet is in support of the target narrative or a 0 indicating it is not")
        negative: int = Field(description="A 1 indicating the tweet is in opposition to the target narrative or a 0 indicating it is not")
        neutral: int = Field(description="A 1 indicating the tweet is neutral to the target narrative or a 0 indicating it is not")
        unsure: int = Field(description="A 1 indicating you are unsure of the text's sentiment or a 0 indicating you are sure")

if __name__ == "__main__":
    file = "saved_data/filtered_data_20250428_194522.csv"
    df = read_media(file)
    print(df[:9])
    summary_model, tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
    target_narrative = "The election was not stolen"
    p = PolarityTester(summary_model, tokenizer, df[:9], target_narrative)
    p.check_polarity()
    print(p.df)
    p.multiply_similarity_and_polarity()
    print(p.df)