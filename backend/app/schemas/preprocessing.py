from pydantic import BaseModel , Field 

class PreprocessingIssue(BaseModel): # "What problem did we find ?"

    column : str
    issue : str 
    description : str | None = None 
    severity : str | None = None



class PreprocessingAction(BaseModel): # "What action could address it ?"

    columns : str  # Which column the action applies to.
    action : str  # The preprocessing operation.
    parameters : dict = Field(default_factory = dict) # Additional information required to execute the action.
    reason : str # Why this action is being considered.

class PreprocessingPlan(BaseModel):
    actions : list[PreprocessingAction] = Field(default_factory = list) 
    reasoning : str 
    source : str 








