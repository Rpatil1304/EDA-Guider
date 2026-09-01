from pydantic import BaseModel


class columnProfile(BaseModel):

    name : str 
    inferred_type : str
    raw_dtype : str

    missing_count : int 
    missing_percentage : float

    unique_count : int
    unique_percentage : float

# Because these statistics don't make sense for every column. (For categorical columns, for example, they don't make sense.)
    meam : float | None = None 
    median : float | None = None
    std : float | None = None
    minimum : float | None = None
    maximum : float | None = None
    skwewness : float | None = None
    kurtosis : float | None = None

    outlier_count : int = 0 
    outlier_percentage : float = 0.0
    lower_bound : float | None = None
    upper_bound : float | None = None

    top_categories : dict[str , int] | None = None
    mode : str | None = None 

    datetime_min : str | None = None
    datetime_max : str | None = None 


