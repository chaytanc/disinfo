import pandas as pd
import numpy as np
import os


def read_media(file):
    """ Returns a pandas dataframe of the file. """
    if file.endswith(".csv"):
        try:
            df = pd.read_csv(file, encoding="utf-8", encoding_errors="ignore")
        except FileNotFoundError:
            raise ValueError(f"Error: The file '{file}' was not found.")
        except pd.errors.EmptyDataError:
            raise ValueError(f"Error: The file '{file}' is empty or corrupted.")
        except Exception as e:
            raise ValueError(f"Error loading file '{file}': {e}")
    elif file.endswith(".txt"):
        try:
            with open(file, "r") as f:
                content = f.read()
                df = pd.DataFrame({"Tweet": [content]})
        except FileNotFoundError:
            raise ValueError(f"Error: The file '{file}' was not found.")
        except pd.errors.EmptyDataError:
            raise ValueError(f"Error: The file '{file}' is empty or corrupted.")
        except Exception as e:
            raise ValueError(f"Error loading file '{file}': {e}")
    else:
        raise ValueError("Unsupported file format. Please provide a .csv or .txt file.")

    return df


def preprocess_context_window(file, smallest_batch_size):
    if file.endswith(".txt"):
        with open(file, "r") as f:
            #TODO batch tweets together somehow -- append previously found narratives to the new batch of tweets? Largest batch possible? very small frequent chunks? Enough to get a general sense of thoughts? Very small then aggregate up multiple times?
            pass
    elif file.endswith(".csv"):
        df = pd.read_csv(file, encoding='utf-8', encoding_errors='ignore')
        # Create n_tweets / smallest_batch_size chunks of tweets / data
        chunks = chunk_it(df, smallest_batch_size)
        return chunks


def chunk_it(array, k):
    """ Turns an array into k chunks of roughly equal size. """
    return np.array_split(array, np.ceil(len(array) / k).astype(int))


def embed_narratives(model, narratives):
    nar_embeds = []
    for narrative in narratives:
        nar_embeds.append(model.encode(narrative, convert_to_tensor=True))
    return nar_embeds


def process_full_tweets(file):
    """ Processes csv files from Junkipedia Twitter data. """
    df = read_media(file)
    # df["Tweet"] = df["post_body_text"] +  "Embedded: " + df["EmbeddedContentText"]
    df["embedded"] = "Embedded content: "
    df["Tweet"] = df[["post_body_text", "embedded", "EmbeddedContentText"]].apply(lambda row: row.dropna().tolist(), axis=1).str[0]
    # df["Datetime"] = pd.to_datetime(df["date"], format="%Y-%m-%d %H:%M:%S")
    df["Datetime"] = pd.to_datetime(df["published_at"], format="%Y-%m-%dT%H:%M:%S.%fZ").dt.floor('s')
    df["id"] = df["PostId"]
    df.to_csv("tweets/full_" + os.path.basename(file))


def add_datetime_column(df):
    # arrange tweets in chronological order based on "Time" column
    if "Datetime" not in df.columns:
        df["Datetime"] = pd.to_datetime(df["Date"], format="%Y-%m-%d %H:%M:%S%z")
    df = df.sort_values(by='Datetime', ascending=True) # no .reset_index(drop=True)
    return df
# TODO final analysis on specific time range (June 01 2015 to present)

process_full_tweets("tweets/tweets_FoxFull.csv")