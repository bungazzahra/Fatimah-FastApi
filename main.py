# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os
from typing import Optional
from fastapi import FastAPI, File, UploadFile
import json
from fastapi.responses import HTMLResponse
import requests
import pandas as pd
from requests import get
from typing import Iterable, Dict, Union, List
from json import dumps
from requests import get
from http import HTTPStatus

app = FastAPI()




StructureType = Dict[str, Union[dict, str]]
FiltersType = Iterable[str]
APIResponseType = Union[List[StructureType], str]

def get_paginated_dataset(filters: FiltersType, structure: StructureType,
                          as_csv: bool = False) -> APIResponseType:
    """
    Extracts paginated data by requesting all of the pages
    and combining the results.

    Parameters
    ----------
    filters: Iterable[str]
        API filters. See the API documentations for additional
        information.

    structure: Dict[str, Union[dict, str]]
        Structure parameter. See the API documentations for
        additional information.

    as_csv: bool
        Return the data as CSV. [default: ``False``]

    Returns
    -------
    Union[List[StructureType], str]
        Comprehensive list of dictionaries containing all the data for
        the given ``filters`` and ``structure``.
    """
    endpoint = "https://api.coronavirus.data.gov.uk/v1/data"

    api_params = {
        "filters": str.join(";", filters),
        "structure": dumps(structure, separators=(",", ":")),
        "format": "json" if not as_csv else "csv"
    }

    data = list()

    page_number = 1

    while True:
        # Adding page number to query params
        api_params["page"] = page_number

        response = get(endpoint, params=api_params, timeout=10)

        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise RuntimeError(f'Request failed: {response.text}')
        elif response.status_code == HTTPStatus.NO_CONTENT:
            break

        if as_csv:
            csv_content = response.content.decode()

            # Removing CSV header (column names) where page 
            # number is greater than 1.
            if page_number > 1:
                data_lines = csv_content.split("\n")[1:]
                csv_content = str.join("\n", data_lines)

            data.append(csv_content.strip())
            page_number += 1
            continue

        current_data = response.json()
        page_data: List[StructureType] = current_data['data']
        
        data.extend(page_data)

        # The "next" attribute in "pagination" will be `None`
        # when we reach the end.
        if current_data["pagination"]["next"] is None:
            break

        page_number += 1

    if not as_csv:
        return data

    # Concatenating CSV pages
    return str.join("\n", data)




def get_data(url):
    response = get(url, timeout=10)
    
    if response.status_code >= 400:
        raise RuntimeError(f'Request failed: { response.text }')
        
    return response.json()




@app.get('/')
def read_root():
    
    return {"hello":"World"}



@app.get("/readapizahra")
def get_body():
    endpoint = (
        'https://api.coronavirus.data.gov.uk/v1/data?'
        'filters=areaType=nation;areaName=england&'
        'structure={"date":"date","newCases":"newCasesByPublishDate"}'
    )
    #Json
    data = get_data(endpoint)
    
    #analisis
    df=pd.json_normalize(data,'data')
    df=df.head(10)
    result=df.to_dict('dict')
    return result

@app.get("/ReadDataCorona")
def get_body():
    query_filters = [
        f"areaType=region"
    ]

    query_structure = {
        "date": "date",
        "name": "areaName",
        "code": "areaCode",
        "daily": "newCasesBySpecimenDate",
        "cumulative": "cumCasesBySpecimenDate"
    }
    json_data = get_paginated_dataset(query_filters, query_structure)
    json_data=json_data[:200]
    return json_data


@app.get("/JumlahCoronaCasesbyMonth")
def get_body():
    query_filters = [
        f"areaType=region"
    ]

    query_structure = {
        "date": "date",
        "name": "areaName",
        "code": "areaCode",
        "daily": "newCasesBySpecimenDate",
        "cumulative": "cumCasesBySpecimenDate"
    }
    json_data = get_paginated_dataset(query_filters, query_structure)


     #PROSES ANALISIS

    df=pd.json_normalize(json_data)
    df=df.head(200)
    #rename columns
    df = df.rename(columns={'name': 'Location', 'daily': 'newCases','cumulative':'cumulativeCases'})
    #ganti datatype date
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    #membuat analisis jumlah corona cases perbulan
    analisis=df.groupby(df['date'].dt.strftime('%B %Y'))['newCases'].sum().to_frame('Jumlah new Cases').reset_index()
    analisis['Rank'] = analisis['Jumlah new Cases'].rank(method='dense', ascending=False)
    analisis
    
    result=analisis.to_dict('dict')
    return result
    
    


@app.post("/uploadfiles/")
def create_upload_files(upload_file: UploadFile = File(...)):
    json_data = json.load(upload_file.file)
#     print(upload_file.file)
    return {"data_in_file": json_data}



if __name__== "__main__":
    uvicorn.run(app,host="0.0.0.0",port=int(os.environ.get('PORT',5000)), log_level="info")
