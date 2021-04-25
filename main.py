# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

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

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]



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
    
    return {"hero":"World"}

# @app.get('/items/{items_id}')
# def read_item(item_id:int,q:Optional[str]=None):
#     return {"item_id":item_id, "q":q}

@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]

# @app.get("/items/{item_id}")
# async def read_item(item_id: str, q: Optional[str] = None):
#     if q:
#         return {"item_id": item_id, "q": q}
#     return {"item_id": item_id}

# @app.post("/uploadcsv/")
# def upload_csv(csv_file: UploadFile = File(...)):
#     df = pd.read_csv(csv_file.file)
#     # do something with dataframe here (?)
#     return {"filename": file.filename}

@app.get("/tampilangka/")
def tampilangka():
    a = 1+2+3
    return {"tes":a}


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
    # print(json_data[:3])
        # analisis
        
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
    
    

    return json_data[:3]





@app.post("/uploadfiles/")
def create_upload_files(upload_file: UploadFile = File(...)):
    json_data = json.load(upload_file.file)
#     print(upload_file.file)
    return {"data_in_file": json_data}

# @app.get("/")
# async def main():
#     content = """
# <body>
# <form action="/files/" enctype="multipart/form-data" method="post">
# <input name="files" type="file" multiple>
# <input type="submit">
# </form>
# <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
# <input name="files" type="file" multiple>
# <input type="submit">
# </form>
# </body>
#     """
#     return HTMLResponse(content=content)