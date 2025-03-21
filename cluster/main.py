 import datetime
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import argparse
import json
import numpy as np
from tqdm import tqdm
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from utils.kcenter_greedy import kCenterGreedy
from datasets import load_dataset


def get_code_embedding(
    data: List[str], model_name: str, batch_size: int
) -> List[Dict[str, Any]]:
    """
    Generate embeddings for a list of code snippets using a sentence transformer model.

    Parameters:
    data (List[str]): A list of code snippets to embed.
    model_name (str): The name of the sentence transformer model to use.
    batch_size (int): The size of the batch for embedding generation.

    Returns:
    List[Dict[str, Any]]: A list of dictionaries with 'text' and 'embedding' keys.
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(data, batch_size=batch_size, show_progress_bar=True)
    res = [{"text": t, "embedding": e.tolist()} for t, e in zip(data, embeddings)]

    return res

def coreset(embeddings: np.ndarray, num: int, seed: int) -> np.ndarray:
    """
    Select a coreset from a set of embeddings using the k-Center Greedy algorithm.

    Parameters:
    embeddings (np.ndarray): An array of embeddings.
    num (int): The number of elements to select for the coreset.

    Returns:
    np.ndarray: An array containing the coreset elements.
    """
    kcg = kCenterGreedy(X=embeddings, y=None, seed=seed)
    batch = kcg.select_batch_(model=None, already_selected=[], N=num)
    return batch


# Set up the argument parser


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
    argparse.Namespace: Parsed arguments as an object.
    """
    parser = argparse.ArgumentParser(
        description="Generate embeddings for code and create a coreset."
    )
    parser.add_argument(
        "--save_path",
        type=str,
        required=True,
        help="Path to save the coreset data.",
    )
    parser.add_argument(
        "--input_path",
        type=str,
        required=True,
        help="Path to save the coreset data.",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4096,
        help="Batch size for embedding generation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )
    parser.add_argument(
        "--subset_size",
        type=int,
        default=0,
        help="Random seed.",
    )
    parser.add_argument(
        "--subset_step",
        type=int,
        default=0,
        help="Random seed.",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="sentence-transformers/all-roberta-large-v1",
        help="Pretrained model name for sentence transformer.",
    )
    parser.add_argument(
        "--coreset_size",
        type=int,
        required=True,
        help="Number of elements to include in the coreset.",
    )

    args = parser.parse_args()
    return args

def get_source_data(filepath: str):
    """
    Load dataset from a local jsonl file.

    Args:
    filepath (str): Path to the local jsonl file.

    Returns:
    Dataset: Loaded dataset.
    """
    dataset = load_dataset('json', data_files=filepath, split='train')
    return dataset

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def main():
    """
    Main function to load data, generate embeddings, create a coreset, and save the results.
    """
    args = parse_args()

    # Load the dataset
    dataset = get_source_data(args.input_path)
    data = dataset["full_content"]

    if args.subset_size>0:
        data=data[args.subset_size*args.subset_step:args.subset_size*(args.subset_step+1)]

    # Ensure the coreset size does not exceed the data size
    if args.coreset_size > len(data):
        raise ValueError("coreset_size exceeds the number of data entries")

    # Get code embeddings
    embeddings = get_code_embedding(data, args.model_name, args.batch_size)

    # Create a coreset from the dataset
    coreset_indices = coreset(
        np.array([example["embedding"] for example in embeddings]),
        args.coreset_size,
        args.seed,
    )

    coreset_data = [dataset[int(idx)] for idx in coreset_indices]

    with open(args.save_path, "w") as f:
        for entry in coreset_data:
            f.write(json.dumps(entry, cls=CustomJSONEncoder) + "\n")

    # Optionally, save the coreset to a file
    # with open(args.save_path, "w") as f:
    #     json.dump(coreset_data, f, indent=4, cls=CustomJSONEncoder)


if __name__ == "__main__":
    main()