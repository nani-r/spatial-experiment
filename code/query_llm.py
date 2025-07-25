#Author: Kent O'Sulivan // osullik@umd.edu

# Core Imports
import os
import json
import argparse
from tqdm import tqdm
import time
from datetime import datetime

# Library Imports
import openai
import google.generativeai as genai
import anthropic
from anthropic import Anthropic
from llamaapi import LlamaAPI


# User Imports
from calculate_distances import GeoCalc
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings



# Classes

class Spatial_LLM_Tester():
    def __init__(self, 
                 oai_api_var_name:str = "OAI_API",
                 gem_api_var_name:str = "GEM_API",
                 ant_api_var_name:str = "ANT_API",
                 met_api_var_name:str = "MET_API",
                 data_directory:os.path = os.path.join("..","data"),
                 results_directory:os.path = os.path.join("..","results")):
        
        #OpenAI 
        self._oai_api_key = self.get_api_key_from_environ_var(var_name=oai_api_var_name)
        self.oai_client = openai.OpenAI(api_key=self._oai_api_key)

        #Google Gemini
        self._gem_api_key = self.get_api_key_from_environ_var(var_name=gem_api_var_name)
        genai.configure(api_key=self._gem_api_key)
        self._gem_client = None

        #Anthropic
        self._ant_api_key = self.get_api_key_from_environ_var(var_name=ant_api_var_name)
        self._ant_client = Anthropic(api_key=self._ant_api_key)

        # #Meta
        self._met_api_key = self.get_api_key_from_environ_var(var_name=met_api_var_name)
        self.met_client = LlamaAPI(self._met_api_key)

        self._data_directory = self.set_data_directory(data_directory=data_directory)
        self.experiment_file = {}
        self._system_prompt = ""
        self._results_directory = self.set_results_directory(results_directory=results_directory)

        #RAG Setup
        self._retriever = self.setup_topological_retriever()
        self.directional_retriever = self.setup_directional_retriever()
        self.toponym_retriever = self.setup_toponym_retriever()
        self.cyclical_retriever = self.setup_cyclical_retriever()



        self.gc=GeoCalc()
        self._relation_type = ''
        self._norm_factor = 0

        self.model_name = ''

    def setup_topological_retriever(self):
        embedding = OpenAIEmbeddings(openai_api_key=self._oai_api_key)
        index_path = "/Users/nani/experiment_paper/Spatial_LLM_Position/australia_spatial_index"
        retriever = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True).as_retriever(search_kwargs={"k":5})

        return retriever

    def setup_directional_retriever(self):
        embedding = OpenAIEmbeddings(openai_api_key=self._oai_api_key)
        index_path = "/Users/nani/experiment_paper/Spatial_LLM_Position/australia_spatial_index"
        retriever = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True).as_retriever(search_kwargs={"k":5})
        return retriever

    def setup_toponym_retriever(self):
        embedding = OpenAIEmbeddings(openai_api_key=self._oai_api_key)
        index_path = "/Users/nani/experiment_paper/Spatial_LLM_Position/australia_spatial_index"
        retriever = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True).as_retriever(search_kwargs={"k":5})

        return retriever

    def setup_cyclical_retriever(self):

            embedding = OpenAIEmbeddings(openai_api_key=self._oai_api_key)
            index_path = "/Users/nani/experiment_paper/Spatial_LLM_Position/australia_spatial_index"
            retriever = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True).as_retriever(search_kwargs={"k":5})

            return retriever


    def retrieve_topological_context(self, question: str) -> str:
        try:
            docs = self._retriever.get_relevant_documents(question)
            return "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"[Topological RAG] Retrieval failed: {e}")
            return "No topological documents found."

    def retrieve_directional_context(self, question: str) -> str:
        try:
            docs = self.directional_retriever.get_relevant_documents(question)
            return "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"[Directional RAG] Retrieval failed: {e}")
            return "No directional documents found."

    def retrieve_toponym_context(self, question: str) -> str:
        try:
            docs = self.toponym_retriever.get_relevant_documents(question)
            return "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"[Toponym RAG] Retrieval failed: {e}")
            return "No toponym documents found."

    def retrieve_cyclical_context(self, question: str) -> str:
        try:
            docs = self.cyclical_retriever.get_relevant_documents(question)
            return "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"[Cyclical RAG] Retrieval failed: {e}")
            return "No cyclical documents found."
          
    def get_api_key_from_environ_var(self, var_name:str):
        try: 
            key= os.environ[var_name]
        except KeyError:
            exit("API Key not found, ensure you run 'echo OAI_API=<your_api_key>' in your shell and try again")

        return key
        
    def check_oai_api_key_valid(self):
        try:
            chat_completion = self.oai_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            model="gpt-3.5-turbo",
            seed=131901,            #Setting seed makes result sampling consistent
            temperature=0           #Setting temprature to 0 minimizes randomness in result.
            )
        except openai.APIConnectionError as e:
            return str(e.status_code)
        
        return chat_completion
    
    def set_data_directory(self, data_directory:os.path)->None:
        if not os.path.exists(data_directory):
            print(f'{data_directory} not found, creating...')
            os.makedirs(data_directory)
        self._data_directory = data_directory
        return data_directory
    
    def get_data_directory(self)->os.path:
        return self._data_directory
    
    def set_results_directory(self, results_directory:os.path)->None:
        if not os.path.exists(results_directory):
            print(f'{results_directory} not found, creating...')
            os.makedirs(results_directory)
        self._results_directory = results_directory
        return results_directory
    
    def get_results_directory(self)->os.path:
        return self._results_directory
    
    def set_system_prompt(self, system_prompt:str)->None:
        self._system_prompt = system_prompt

    def get_system_prompt(self)->str:
        return(self._system_prompt)
    
    def load_question_file_to_dict(self, filename:str)->dict:
        file_path = os.path.join(self.get_data_directory(), filename)
        print(f"Trying to load from {file_path}...")
        try:
            with open(file_path, 'r') as f:
                experiment_dict = json.load(f)
                print("Success!")
        except:
            exit(f"Unable to Load {file_path}")
        
        self._relation_type = experiment_dict['metadata']['relation_type']
        self.experiment_file = experiment_dict 
        return experiment_dict
    
    def get_filename(self)->str:
        return(self.experiment_file['metadata']['file_name'])
    
    def get_relation(self)->str:
        return(self.experiment_file['metadata']['relation_type'])


    def ask_single_question(self, question:str, 
                            model="gpt-3.5-turbo", 
                            seed:int=131901, 
                            temp:int=0)->str:
        
        relation = self._relation_type.casefold()
    
        if "topological" in relation:
            docs = self._retriever.get_relevant_documents(question)
        elif "directional" in relation:
            docs = self.directional_retriever.get_relevant_documents(question)
        elif "order" in relation or "cyclical" in relation:
            docs = self.cyclical_retriever.get_relevant_documents(question)
        elif "toponym" in relation:
            docs = self.toponym_retriever.get_relevant_documents(question)
        else:
            docs = []

        # print("\n=== Retrieved Docs ===")
        # for i, doc in enumerate(docs):
        #     print(f"\n[{i+1}] {doc.page_content}")

        context = "\n".join([doc.page_content for doc in docs])

        #final_system_prompt = f"{self._system_prompt}\n\nRelevant Context:\n{context}"
        final_system_prompt = (
        f"{self._system_prompt}"
        "Answer the question with only the essential information." 
        f"Relevant Context that may help:\n{context}"
    )
        
        chat_completion = self.oai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": question}
            ],
            model=model,
            seed=seed,
            temperature=temp
        )

        result = {
            'question': question,
            'answer': chat_completion.choices[0].message.content.casefold()
        }

        return result
    
    def ask_multiple_questions(self,    questions:dict, 
                                        model:str="gpt-3.5-turbo",
                                        seed:int=131901,
                                        temp:int=0)->dict:
        results = {}
        print(f"Running Experiment querying {model} API")
        for question in tqdm(questions.keys()):
            q = questions[question]['question']
            a = self.ask_single_question(question=q, 
                                         model=model, 
                                         seed=seed,
                                         temp=temp)
            results[question] = a

        return results
    
    def evaluate_answer(self, gt_answers:list[str], pred_answer:str):

        lc_dict = {}

        for k,v in gt_answers.items():
            lc_dict[k.casefold()] = v
        pred_answer = pred_answer.replace('.','')

        if pred_answer.casefold() in lc_dict:
            return(lc_dict[pred_answer.casefold()])
        else:
            return 0
        
    def evaluate_toponym_answer(self, gt_answers:list[str], pred_answer:str):
        lc_dict = {}
        admin_levels = set()

        for k,v in gt_answers.items():
            lc_dict[k.casefold()] = v
        pred_answer = pred_answer.replace('.','')

        commagroup = pred_answer.split(",")
        for loc in commagroup:
            if loc.casefold().strip() in lc_dict:
                admin_levels.add(lc_dict[loc.casefold().strip()])

        raw_score = len(admin_levels)
        score = raw_score * (raw_score/len(commagroup))

        return((score, list(admin_levels)))
        

    def evaluate_all_answers(self, gt_answers:dict, results:dict)->dict:

        print(f"Evaluating the answers...")
        for result in tqdm(results.keys()):
            score = self.evaluate_answer(gt_answers=gt_answers[result]['answers'], 
                                    pred_answer=results[result]['answer'])
            if score > 0:
                results[result]['correct'] = 1
            else:
                results[result]['correct'] = 0
            
            results[result]['score'] = score
        
        return results
        
    def evaluate_all_toponym_answers(self, gt_answers:dict, results:dict):
        print(f"Evaluating the answers...")
        for result in tqdm(results.keys()):
            score, admin_levels = self.evaluate_toponym_answer(gt_answers=gt_answers[result]['answers'], 
                                    pred_answer=results[result]['answer'])
            if score > 0:
                results[result]['correct'] = 1
            else:
                results[result]['correct'] = 0
            
            results[result]['score'] = score
            results[result]['admin_levels'] = admin_levels
        
        return results
    
    def evaluate_all_metric_answers(self, gt_answers:dict, results:dict, norm_factor=4000):
        #Norm factor used to normalize distances. Set roughly equal to diameter of country. 
        
        print(f"Evaluating the answers...")
        for result in tqdm(results.keys()):

            #Reset Vars:
            gt_dist = None
            pred_dist = None
            score = 0 
            ratio = None
            results[result]['correct'] = 0
            sim = None
            results[result]['prediction'] = results[result]['answer']

            if results[result]['answer'] is None or results[result]['answer'] =="error":
                gt_dist = None
                pred_dist = None
                score = 0 
                ratio = None
                results[result]['correct'] = 0
                sim = "error"
                results[result]['prediction'] = results[result]['answer']

                results[result]['answer'] = sim
                results[result]['example_dist'] = gt_dist
                results[result]['predicted_dist'] = pred_dist
                results[result]['prediction'] = temp 
                results[result]['ratio'] = ratio 
                results[result]['score'] = score

                return results
            
            data = gt_answers[result]['locations']
            try:
                gt_dist, pred_dist, ratio, sim = self.gc.calculate_nearness(loc1a = data['source_example'],
                                                        loc1b = data['dest_example'],
                                                        loc2a = data['source_test'],
                                                        loc2b = results[result]['answer'],
                                                        norm_factor=norm_factor)
                score = self.evaluate_answer(gt_answers=gt_answers[result]['answers'], 
                                        pred_answer=sim)
                
                if score > 0:
                    results[result]['correct'] = 1
                else:
                    results[result]['correct'] = 0
            
            except AttributeError as e:
                print("ERROR", e)
                gt_dist = None
                pred_dist = None
                score = 0 
                ratio = None
                results[result]['correct'] = 0
                sim = "error"
            
            temp = results[result]['answer']

            results[result]['answer'] = sim
            results[result]['example_dist'] = gt_dist
            results[result]['predicted_dist'] = pred_dist
            results[result]['prediction'] = temp 
            results[result]['ratio'] = ratio 
            results[result]['score'] = score

        
        return results

    
    def run_experiment(self, filename:os.path, model:str="gpt-3.5-turbo", seed:int=131901, temp:int=0)->dict:

        experiment_dict = self.load_question_file_to_dict(filename=os.path.join(self.get_data_directory(), filename))
        
        self.set_system_prompt(experiment_dict['metadata']['system_prompt'])

        results = self.ask_multiple_questions(questions=experiment_dict['questions'],model=model,seed=seed,temp=temp)

        if 'metric' in self._relation_type.casefold():
            self._norm_factor = experiment_dict['metadata']['norm_factor']
            evaluated = self.evaluate_all_metric_answers(gt_answers=experiment_dict['questions'], results=results,norm_factor=self._norm_factor)
        elif 'toponym' in self._relation_type.casefold():
            evaluated = self.evaluate_all_toponym_answers(gt_answers=experiment_dict['questions'], results=results)
        else:
            evaluated = self.evaluate_all_answers(gt_answers=experiment_dict['questions'], results=results)

        to_return = {
                        "metadata":{
                            "model": model, 
                            "seed":seed,
                            "temperature":temp,
                            "relation_type" : experiment_dict['metadata']['relation_type'],
                            "system_prompt" : experiment_dict['metadata']['system_prompt'],
                            "experiment time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            },
                        "results": evaluated
                    }

        return to_return
    
    def save_results_to_file(self, results):

        filename = f"results_{results['metadata']['model']}_{results['metadata']['relation_type']}.json"

        filepath = os.path.join(self.get_results_directory(),filename)

        print(f"Trying to save to {filepath}")

        try:
            with open(filepath, "w") as f:
                print(f'Saved to {filepath}')
                json.dump(results,f,indent=3)
        except Exception as e:
            print("Unable to save to File -- check and try again", e)

    # # # # # # # # #
    #GOOGLE
    # # # # # # # # #

    def list_available_gemini_models(self)->str:
        model_list = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model_list.append(m.name)

        return (model_list)
    
    def set_google_model(self, model_name:str)->str:

        self._gem_client = genai.GenerativeModel(model_name)
        return self._gem_client.model_name
    
    def simple_query_gemini(self, message:str, temp:float=0.0)->str:
        try:
            response = self._gem_client.generate_content(message,
                                                         generation_config=genai.types.GenerationConfig(
                                                        # Only one candidate for now.
                                                        candidate_count=1,
                                                        temperature=temp)
                                                )
            return response.text.strip()
        except Exception as e:
            print(f"SKIPPING -- Unable to Query{self._gem_client.model_name}", e)
            return ("ERROR")
        
    def query_gemini_with_system_prompt(self, message:str, temp:float=0.0):
        messages_gemini = []
        system_promt = f"**{self._system_prompt}**" #No system prompt in Gemini, so we approximate
        messages_gemini.append({'role': 'user', 'parts': [message]})
        if system_promt:
            messages_gemini[0]['parts'].insert(0, f"*{system_promt}*")
        response = self.simple_query_gemini(messages_gemini, temp=temp)
        
        return response
    
    def ask_gemini_single_question(self, question:str, 
                            model="gemini-1.0-pro", 
                            seed:int=131901, 
                            temp:int=0)->str:
        
        self.set_google_model(model_name=model)
        chat_completion = self.query_gemini_with_system_prompt(message=question, temp=temp)
        
        result = {
                    'question'      : question,
                    'answer'        : chat_completion.casefold()
                }
        
        return(result)
    
    def ask_gemini_multiple_questions(self,    questions:dict, 
                                        model:str="gemini-1.0-pro",
                                        seed:int=131901,
                                        temp:int=0)->dict:
        results = {}
        print(f"Running Experiment querying {model} API")
        for question in tqdm(questions.keys()):
            q = questions[question]['question']
            a = self.ask_gemini_single_question(question=q, 
                                         model=model, 
                                         seed=seed,
                                         temp=temp)
            results[question] = a

        return results
    
    def run_gemini_experiment(self, filename:os.path, model:str="gemini-1.0-pro", seed:int=131901, temp:int=0)->dict:

        experiment_dict = self.load_question_file_to_dict(filename=os.path.join(self.get_data_directory(), filename))
        
        self.set_system_prompt(experiment_dict['metadata']['system_prompt'])

        results = self.ask_gemini_multiple_questions(questions=experiment_dict['questions'],model=model,seed=seed,temp=temp)

        if 'metric' in self._relation_type.casefold():
            self._norm_factor = experiment_dict['metadata']['norm_factor']
            evaluated = self.evaluate_all_metric_answers(gt_answers=experiment_dict['questions'], results=results,norm_factor=self._norm_factor)
        elif 'toponym' in self._relation_type.casefold():
            evaluated = self.evaluate_all_toponym_answers(gt_answers=experiment_dict['questions'], results=results)
        else:
            evaluated = self.evaluate_all_answers(gt_answers=experiment_dict['questions'], results=results)

        to_return = {
                        "metadata":{
                            "model": model, 
                            "seed":seed,
                            "temperature":temp,
                            "relation_type" : experiment_dict['metadata']['relation_type'],
                            "system_prompt" : experiment_dict['metadata']['system_prompt'],
                            "experiment time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            },
                        "results": evaluated
                    }

        return to_return
    
    # # # # # # # # # #
    # ANTHROPIC
    # # # # # # # # # #
    
    def check_ant_api_key_is_valid(self,model)->str:
        try:
            chat_completion = self._ant_client.messages.create(
            max_tokens=128,
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            model=model,
            temperature=0           #Setting temprature to 0 minimizes randomness in result.
            )
        except anthropic.APIConnectionError as e:
            return str(e.status_code)
        
        return chat_completion
    
    def ask_ant_single_question(self, question:str, 
                            model="claude-3-opus-20240229", 
                            seed:int=131901, 
                            temp:int=0)->str:
        
        chat_completion = self._ant_client.messages.create(
            max_tokens=128,
            system=self._system_prompt,
            messages=[
                        {
                            "role": "user", 
                            "content": f"{question}"}
                    ],
            model=model,          #Set the model to use
            temperature=temp      #Setting temprature to 0 minimizes randomness in result.
            )
        
        result = {
                    'question'      : question,
                    'answer'        : chat_completion.content[0].text.casefold()
                }
        return(result)
    
    def ask_ant_multiple_questions(self,    questions:dict, 
                                        model:str="claude-3-opus-20240229",
                                        seed:int=131901,
                                        temp:int=0)->dict:
        results = {}
        print(f"Running Experiment querying {model} API")
        for question in tqdm(questions.keys()):
            q = questions[question]['question']
            a = self.ask_ant_single_question(question=q, 
                                         model=model, 
                                         seed=seed,
                                         temp=temp)
            results[question] = a

        return results
    
    def run_anthropic_experiment(self, filename:os.path, model:str="claude-3-opus-20240229", seed:int=131901, temp:int=0)->dict:

        experiment_dict = self.load_question_file_to_dict(filename=os.path.join(self.get_data_directory(), filename))
        
        self.set_system_prompt(experiment_dict['metadata']['system_prompt'])

        results = self.ask_ant_multiple_questions(questions=experiment_dict['questions'],model=model,seed=seed,temp=temp)

        if 'metric' in self._relation_type.casefold():
            self._norm_factor = experiment_dict['metadata']['norm_factor']
            evaluated = self.evaluate_all_metric_answers(gt_answers=experiment_dict['questions'], results=results,norm_factor=self._norm_factor)
        elif 'toponym' in self._relation_type.casefold():
            evaluated = self.evaluate_all_toponym_answers(gt_answers=experiment_dict['questions'], results=results)
        else:
            evaluated = self.evaluate_all_answers(gt_answers=experiment_dict['questions'], results=results)

        to_return = {
                        "metadata":{
                            "model": model, 
                            "seed":seed,
                            "temperature":temp,
                            "relation_type" : experiment_dict['metadata']['relation_type'],
                            "system_prompt" : experiment_dict['metadata']['system_prompt'],
                            "experiment time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            },
                        "results": evaluated
                    }

        return to_return
    
    

    # # # # # # # # # #
    # META
    # # # # # # # # # #
            
    def check_met_api_key_is_valid(self,model)->str:
        try:
            message = {
                "model": model,
                "messages": [
                    {
                    "role": "user",
                    "content": "Say this is a test",
                }
                ]
                }
            chat_completion = self.met_client.run(
            message,
            )
        except anthropic.APIConnectionError as e:
            return str(e.status_code)
        # print(json.dumps(chat_completion.json(),indent=2))
        return chat_completion
    
    def ask_met_single_question(self, question:str, 
                            model="llama3-70b", 
                            seed:int=131901, 
                            temp:float=0.0)->str:
        
        message = {
            "model":model,
            "temperature":temp,
            "messages":[
                        {
                            "role": "system", 
                            "content": f"{self._system_prompt}"},
                        {
                            "role": "user", 
                            "content": f"{question}"}
                    ]
        }        
        
        #Api fails frequently and breaks the json decoder, while loop and error handling accounts for API instability.
        chat_completion = None
        while chat_completion is None:
            try:
                chat_completion = self.met_client.run(message)
                if chat_completion is not None: 
                    break
            except Exception as e:
                print("Error occured -- Detail:",e)
            print('null response... trying again in 5')
            time.sleep(5)
        
        cc = chat_completion.json()
                
        result = {
                    'question'      : question,
                    'answer'        : (cc['choices'][0]['message']['content']).casefold()
                }
        return(result)
    
    def ask_met_multiple_questions(self,    questions:dict, 
                                        model:str="llama3-70b",
                                        seed:int=131901,
                                        temp:int=0)->dict:
        results = {}
        print(f"Running Experiment querying {model} API")
        for question in tqdm(questions.keys()):
            q = questions[question]['question']
            a = self.ask_met_single_question(question=q, 
                                         model=model, 
                                         seed=seed,
                                         temp=temp)
            results[question] = a

        return results
    
    def run_meta_experiment(self, filename:os.path, model:str="llama3-70b", seed:int=131901, temp:int=0)->dict:

        experiment_dict = self.load_question_file_to_dict(filename=os.path.join(self.get_data_directory(), filename))
        
        self.set_system_prompt(experiment_dict['metadata']['system_prompt'])

        results = self.ask_met_multiple_questions(questions=experiment_dict['questions'],model=model,seed=seed,temp=temp)

        if 'metric' in self._relation_type.casefold():
            self._norm_factor = experiment_dict['metadata']['norm_factor']
            evaluated = self.evaluate_all_metric_answers(gt_answers=experiment_dict['questions'], results=results,norm_factor=self._norm_factor)
        elif 'toponym' in self._relation_type.casefold():
            evaluated = self.evaluate_all_toponym_answers(gt_answers=experiment_dict['questions'], results=results)
        else:
            evaluated = self.evaluate_all_answers(gt_answers=experiment_dict['questions'], results=results)

        to_return = {
                        "metadata":{
                            "model": model, 
                            "seed":seed,
                            "temperature":temp,
                            "relation_type" : experiment_dict['metadata']['relation_type'],
                            "system_prompt" : experiment_dict['metadata']['system_prompt'],
                            "experiment time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            },
                        "results": evaluated
                    }

        return to_return
    
    def print_results(self, results:dict, model:str)->None:

        correct = 0
        incorrect = 0
        score = 0
        unanswered = 0
        total_questions = 0
        for result in results["results"].keys():
            total_questions +=1
            correct += results["results"][result]['correct']
            score += results["results"][result]['score']
            if results["results"][result]['correct'] == 0:
                if results["results"][result]['answer'] in ['error', 'icatq']:
                    unanswered +=1
                else:
                    incorrect += 1

        print(f"\n########## RESULTS: {model} ##########")
        print("TOTAL QUESTIONS:", total_questions)
        print("SCORE:\t\t", score)
        print("CORRECT:\t", correct,"\t", round((correct/total_questions)*100,2),"%")
        print("INCORRECT:\t", incorrect,"\t", round((incorrect/total_questions)*100,2),"%")
        print("UNANSWERED:\t", unanswered,"\t", round((unanswered/total_questions)*100,2),"%")
        print("#####################\n")


    
# Main

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()

    argparser.add_argument("--data_directory", 
                           help="path to directory that question files are located", 
                           type=str,
                           required=False,
                           default="../data")
    argparser.add_argument("--results_directory",
                           help="directory for the results to be saved", 
                           type=str, 
                           required=False, 
                           default="../results")
    argparser.add_argument("--quiz_file",
                           help="File name of the quiz file to test, including extension",
                           type=str,
                           required=True)
    argparser.add_argument("--model_family", 
                           help="Model Family ['OPENAI', 'GOOGLE', 'ANTHROPIC', 'META']",
                           type=str, 
                           required=True)
    argparser.add_argument("--model", 
                           help="Model to use from ['gpt-4o','gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo','gemini-1.0-pro',' gemini-1.5-flash','gemini-1.5-pro', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307', 'llama3-70b','llama3-8b', 'mixtral-8x22b-instruct', 'mistral-7b-instruct']",
                           type=str, 
                           required=True)
    argparser.add_argument("--seed",
                           help='Seed to use to improve reproducibility of results. Integer. Only applies to OPENAI family models', 
                           type=int, 
                           required=False, 
                           default=131901)
    argparser.add_argument("--temp", 
                           help="set the temperature of the model. 0 is low, 2 is high", 
                           type=int, 
                           required=False, 
                           default=0)
    
    flags = argparser.parse_args()

    if flags.model_family == "OPENAI":
        tester = Spatial_LLM_Tester(data_directory=flags.data_directory,
                                    results_directory=flags.results_directory)
        results = tester.run_experiment(filename=flags.quiz_file,
                                        model=flags.model,
                                        seed=flags.seed,
                                        temp=flags.temp)
    
    elif flags.model_family == "GOOGLE":
        tester = Spatial_LLM_Tester(data_directory=flags.data_directory,
                                    results_directory=flags.results_directory)
        results = tester.run_gemini_experiment(filename=flags.quiz_file,
                                        model=flags.model,
                                        seed=flags.seed,
                                        temp=flags.temp)
        
    elif flags.model_family == "ANTHROPIC":
        tester = Spatial_LLM_Tester(data_directory=flags.data_directory,
                                    results_directory=flags.results_directory)
        results = tester.run_anthropic_experiment(filename=flags.quiz_file,
                                        model=flags.model,
                                        seed=flags.seed,
                                        temp=flags.temp)
    
    elif flags.model_family == "META":
        tester = Spatial_LLM_Tester(data_directory=flags.data_directory,
                                    results_directory=flags.results_directory)
        results = tester.run_meta_experiment(filename=flags.quiz_file,
                                        model=flags.model,
                                        seed=flags.seed,
                                        temp=flags.temp)
    
        
    tester.save_results_to_file(results=results)
    tester.print_results(results, flags.model)

# E.g. Run a test on topological contains using gpt-3.5-turbo:
# python query_llm.py --quiz_file topological_contains.json --model_family OPENAI --model gpt-3.5-turbo


# if __name__ == "__main__":
#     
#     tester = Spatial_LLM_Tester()

#     
#     tester.set_system_prompt("You are a helpful geographic assistant. Use the retrieved context to answer questions about Australian geography.")

#     # Example questions for each relation type you support
#     test_questions = {
#         "topological": "Does the Molonglo River intersect the Australian Capital Territory?",
#         "directional": "Is Sydney north or south of Melbourne?",
#         "toponym": "What is another name for Fraser Island?",
#         "cyclical": "Is moving from Fraser Island to Alice Springs clockwise or counter-clockwise relative to a centroid in Albury-Wodonga?"
#     }

#     for relation_type, question in test_questions.items():
#         print(f"\n=== Testing relation: {relation_type} ===")
#         
#         tester._relation_type = relation_type
        
#         
#         result = tester.ask_single_question(question)
        
#         
#         print(f"Question: {result['question']}")
#         print(f"Answer: {result['answer']}")
