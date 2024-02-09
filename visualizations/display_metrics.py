"""Get metrics from TrustyAI Service"""
from typing import List, Optional, Any, Union

import json
import os
import pandas as pd
import requests
import subprocess
import datetime as dt

def json_to_df(
        data_path: str, 
        batch_list: List[int]
    ) -> pd.DataFrame: 
    """
    Converts batched data in json files to a single pandas DataFrame
    """
    df = pd.DataFrame()
    for batch in batch_list:
        file = data_path + f'{batch}.json'
        with open(file) as train_file:
            batch_data = json.load(train_file)['inputs'][0]['data']
            batch_df = pd.DataFrame.from_dict(batch_data)
            df = pd.concat([df, batch_df])
    return df

def df_to_json(
        df: pd.DataFrame, 
        name: str, 
        json_file: str
    ) -> None:
    """
    Converts pandas DataFrame to json file
    """
    if str(df.dtypes[0]) == 'float64':
        data_type = 'FP64'
        
    inputs = [{"name": name, "shape": list(df.shape), "datatype": data_type, "data": df.values.tolist()}]
    data_dict = {"inputs": inputs}

    # data_dict = {'model_name': model_name, 'data_tag': data_tag, 'requests': {'inputs': inputs}}
 
    with open(json_file, "w") as outfile: 
        json.dump(data_dict, outfile)
        print('Dataframe successfully converted to json file')
    

class displayMetrics:
    def __init__(self, token):
        self.token = token
        self.trusty_url = 'https://' + (subprocess.check_output('oc get route/trustyai-service --template={{.spec.host}}', shell=True)).decode()
        self.thanos_url = 'https://' + (subprocess.check_output('oc get route thanos-querier -n openshift-monitoring --template={{.spec.host}}', shell=True)).decode()
        self.headers = {"Authorization": "Bearer " + token}

        print(f'TRUSTY ROUTE: {self.trusty_url}')
        print(f'THANOS QUERIER HOST: {self.thanos_url}')
    
  
    # def df_to_json(self, model_name, data_tag, name, df, data_path):
    #     """
    #     Converts pandas dataframe to json file

    #     :param model_name: name of the model 
    #     :type: string 
    #     :param data_tag: optional tag to specifiy whether data is for model training or testing
    #     :type: string
    #     """
    #     if str(df.dtypes[0]) == 'float64':
    #         data_type = 'FP64'
        
    #     inputs = [{'name': name, 'shape': list(df.shape), 'datatype': data_type, 'data': df.values.tolist()}]
    #     data_dict = {'model_name': model_name, 'data_tag': data_tag, 'requests': {'inputs': inputs}}
        
    #     with open(json_file, "w") as outfile: 
    #         json.dump(data_dict, outfile)
    #     print('Dataframe successfully converted to json file')
    
    def upload_payload_data(
            self, 
            json_file: str
        ) -> None:
        """
        Uploads data to TrustyAi '/data/upload' endpoint
        """
        self.headers['Content-Type'] = 'application/json'
        payload = open(json_file, 'r')
        r = requests.post(f'{self.trusty_url}/data/upload', headers=self.headers, data=payload, verify=False)
        payload.close()
        print('Data sucessfully uploaded to TrustyAI service')


    # def run_model_inference(self, model_name, df, json_file, batch_size):
    #     MODEL_ROUTE = 'https://' + subprocess.check_output(f'oc get route/{model_name}' + '--template={{.spec.host}}')
    #     self.headers['Content-Type'] = 'application/json'

        
    #     # batch_list = []
    #     # for batch in batch_list:
    #     #     json_file = f'data/data_batches/{batch}json'
    #     #     with open(json_file, 'r') as file:
    #     #         data = file.read()
    #     #         r = requests.post(
    #     #             MODEL_ROUTE,
    #     #             headers = self.headers, 
    #     #             data = data, 
    #     #             verify = False
    #     #             )
        
    #     # split df into chuncks according to batch size
    #     i = 0 
    #     while i != len(df) - (batch_size + 1):
    #         df_chunk = df.iloc[:, i: batch_size + 1] 
    #     # convert to json 
    #         data = df_to_json(
    #             model_name,
    #             data_tag, 
    #             name, 
    #             df,
    #             json_file
    #             )
    #     # send data to model
    #         r = requests.post(
    #             MODEL_ROUTE,
    #             headers = self.headers, 
    #             data = data, 
    #             verify = False
    #         )
                   

        # print(r.text)
    
    def get_model_metadata(self):
        """
        Retrives model data from TrustyAI 
        """
        self.headers['Content-Type'] = 'application/json'
        r = requests.get(f'{self.trusty_url}/info', headers=self.headers, verify=False)
        model_metadata = json.loads(r.text)
        return model_metadata

    def label_data_fields(self, name_mapping_script):
        """
        """
        # remember to enable read/write access
        os.system(name_mapping_script)
        r = requests.get(f'{self.trusty_url}/info')
        info = json.loads(r.text)[0]
        print(' ')
        for k, v in info['data']['inputSchema']['nameMapping'].items():
            print(f'{k} -> {v}')
        return 

    def get_metric_request(self, data, metric, reoccuring):
        self.headers['Content-Type'] =  'application/json'
        if reoccuring:
            r = requests.post(f'{self.trusty_url}/metrics/{metric}/request', headers=self.headers, json=data)
        else: 
            r = requests.post(f'{self.trusty_url}/metrics/{metric}', headers=self.headers, json=data)
        return r.text
        
    # def schedule_identity(self):
    #     return

    def get_metric_data(
            self, 
            namespace, 
            metric, 
            range
        ) -> pd.DataFrame:
        """
        Get metric data for a range in time
        """
        params = {
            "query": "{metric}{{namespace='{namespace}'}}{range}".format(metric=metric,namespace=namespace, range=range)
        }
        
        # make the GET request
        r = requests.get(f'{self.thanos_url}/api/v1/query?', headers=self.headers, params=params, verify=False)

        # vheck if the request was successful
        if r.status_code == 200:
            # Parse the JSON rand extract the desired data
            data_dict = json.loads(r.text)['data']['result'][0]['values']
            df = pd.DataFrame(data_dict, columns=['timestamp', metric])
            df['timestamp'] = df['timestamp'].apply(lambda epoch: dt.datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S'))
            return df
        else:
            print(f"Error {r.status_code}: {r.reason}")



    

