from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal , Optional
import json 

app = FastAPI()

class Patient(BaseModel):
    id: Annotated[str , Field(..., description="ID of the Patient" , example='P001')]
    name: Annotated[str , Field(..., description="Name of the Patient")]
    city: Annotated[str, Field(..., description="Name of the City where the patient lives")]
    age: Annotated[int , Field(..., description="Age of the Patient" , ge=0)]
    gender: Annotated[Literal['Male', 'Female', 'Other'] , Field(..., description="Gender of the Patient")]
    height: Annotated[float, Field(..., description="Height of the Patient in meters" , gt=0)]
    weight: Annotated[float, Field(..., description="Weight of the Patient in kilograms" , gt=0)]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / (self.height ** 2) , 2)
        return bmi
    
    @computed_field
    @property
    def verdict(self) ->str:
        if self.bmi < 18.5:
            return 'Underweight'
        elif 18.5 <= self.bmi < 25:
            return 'Normal weight'
        elif 25 <= self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'
        

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str] , Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int] , Field(default=None , ge=0)]
    gender: Annotated[Optional[Literal['Male', 'Female', 'Other']] , Field(default=None)]
    height: Annotated[Optional[float], Field(default=None , gt=0)]
    weight: Annotated[Optional[float], Field(default=None , gt=0)]


def load_data():
    with open('patients.json' , 'r') as f:
        data = json.load(f)

    return data

def save_data(data):
    with open('patients.json' , 'w') as f:
        json.dump(data, f, indent=4)


@app.get("/")
def root():
    return {'message': 'Patient Management System API.'}


@app.get("/about")
def about():
    return {'message': 'A fully functional API to manage Patients Records.'}


@app.get("/view_patient")
def view():

    # Load all the patient
    data = load_data()

    return data 


@app.get("/view_patient/{patient_id}")

def view_patient(patient_id: str = Path(..., description="ID of the Patient" , example='P001')):
    
    data = load_data()

    # Find the patient with the given id
    if patient_id in data:
        return data[patient_id]
    
    raise HTTPException(status_code=404 , detail= 'Patient Not Found!')  


@app.get("/sort_patients")
def sort_patients(sort_by: str = Query(..., description="Sort on the basis of height , weight , bmi") , order:str = Query('asc' , description="Sort in Ascending (asc) or Descending Order (desc)" , example='asc')):
    
    sort_by = sort_by.lower()
    order = order.lower()
    valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400 , detail = f'Invalid field, Select from {valid_fields}')
    if order not in ['asc' , 'desc']:
        raise HTTPException(status_code=400 , detail = 'Invalid order, select between Ascending (asc) or Descending (desc)')
    
    data = load_data()

    sort_order = False if order == 'asc' else True 
    sorted_data = sorted(data.values() , key = lambda x:x.get(sort_by , 0) , reverse = sort_order)

    return sorted_data


@app.post("/create")
def create_patient(patient: Patient):

    data = load_data()

    if patient.id in data:
        raise HTTPException(status_code=400, detail=f"Patient {patient.id} already exists!")
    
    data[patient.id] = patient.model_dump(exclude=['id'])

    save_data(data)

    return JSONResponse(status_code=201, content={"message": f"Patient {patient.id} created successfully!"})


@app.put("/edit/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found!")
    
    existing_patient_info = data[patient_id]
    update_patient_info = patient_update.model_dump(exclude_unset=True)

    for key, value in update_patient_info.items():
        existing_patient_info[key] = value

    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)
    existing_patient_info = patient_pydantic_obj.model_dump(exclude=['id'])

    data[patient_id] = existing_patient_info

    save_data(data)

    return JSONResponse(status_code=200, content={"message": f"Patient {patient_id} updated successfully!"})


@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found!")
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content={"message": f"Patient {patient_id} deleted successfully!"})

