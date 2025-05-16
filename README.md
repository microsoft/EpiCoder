# Project

This repository contains the implementation of **Epicoder**, a pipeline designed for code instruction synthesis, encompassing diverse and complex code generation. This work is associated with the paper:  
**[EpiCoder: Encompassing Diversity and Complexity in Code Generation](https://arxiv.org/abs/2501.04694).**  The data can be found in
**[EpiCoder-func-380k on Hugging Face](https://huggingface.co/datasets/microsoft/EpiCoder-func-380k)**  


## Pipeline Overview  

The Epicoder pipeline consists of multiple stages, starting from raw code feature extraction and evolving through code generation, debugging, and testing. Below is a step-by-step breakdown of the pipeline:  

### **Setup**  
Before running the pipeline, set up the `PYTHONPATH`:  

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
```

### **Steps in the Pipeline**  

#### **1. Feature Extraction**  
- `python extract/extract_features.py`  
  Extracts features from raw code.  
- `python extract/extract_frequency_count.py`  
  Counts the frequency of features and identifies the top frequent features, saving the results as a JSON file.  
- `python extract/extract_separate_frequency.py`  
  Separates and saves feature frequencies and features individually.  

#### **2. Feature Evolution**  
- `python evol/feature_evol.py`  
  Evolves the features based on the extracted data.  
- `python evol/merge_expanded_features.py`  
  Merges the evolved features with the original ones.  

#### **3. Instruction and Code Generation**  
- `python gen/gen_question.py`  
  Generates questions or tasks based on the feature set.  
- `python gen/gen_code.py`  
  Generates code according to the tasks created.  

#### **4. Debugging**  
- `python debug/run_test_iter0.py`  
  Runs in a Docker environment to identify correct code outputs.  
- `python debug/run_test_with_debug_multi_turn.py`  
  Tests the code with multiple debugging iterations.  

#### **5. Data Collection for Training**  
- `python utils/get_train_data.py`  
  Saves correct codes as a JSON file for further analysis or training.  

## Running the Pipeline  

Make sure to follow the steps in the pipeline to ensure smooth code generation and testing. The Docker environment is used to validate the generated code.  

For more details, refer to the [Epicoder paper](https://arxiv.org/abs/2501.04694).

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
