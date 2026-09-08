import pandas as pd

from app.profiling.dataset_profiler import profile_dataset


from app.preprocessing.rule_engine import (
    generate_preprocessing_plan
)

def create_messy_dataset() -> pd.DataFrame:
    """
    Create a deliberately messy dataset for testing
    the profiling pipeline.
    """

    data = {

    # --------------------------------------------------
    # 1. Potential ID
    # --------------------------------------------------

    "Customer_ID": [
        "C001",
        "C002",
        "C003",
        "C004",
        "C005",
        "C006",
        "C007",
        "C008",
        "C009",
        "C010",
        "C011",
        "C012",
        "C013",
        "C014",
        "C015",
    ],


    # --------------------------------------------------
    # 2. Numeric values stored as strings
    # --------------------------------------------------

    "Age": [
        "25",
        "30",
        " 35 ",
        "40",
        "NA",
        None,
        "45",
        "50",
        "29",
        "31",
        "42",
        "38",
        "27",
        "33",
        "36",
    ],


    # --------------------------------------------------
    # 3. Numeric column + outlier
    # --------------------------------------------------

    "Salary": [
        25000,
        30000,
        35000,
        40000,
        45000,
        50000,
        55000,
        1000000,
        32000,
        37000,
        41000,
        46000,
        52000,
        58000,
        60000,
    ],


    # --------------------------------------------------
    # 4. Case variations + whitespace
    # --------------------------------------------------

    "City": [
        "Pune",
        "pune",
        "Mumbai",
        " Mumbai ",
        "Delhi",
        "Delhi",
        "Bangalore",
        "PUNE",
        "mumbai",
        "Delhi ",
        "BANGALORE",
        "Pune",
        "pune ",
        "Mumbai",
        "Delhi",
    ],


    # --------------------------------------------------
    # 5. Empty + null-like values
    # --------------------------------------------------

    "Status": [
        "Active",
        "Active",
        "Inactive",
        "Active",
        "",
        "NA",
        "Inactive",
        None,
        "active",
        "ACTIVE",
        "unknown",
        "Inactive",
        "N/A",
        "Active",
        " ",
    ],


    # --------------------------------------------------
    # 6. Constant column
    # --------------------------------------------------

    "Constant_Column": [
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
        "YES",
    ],


    # --------------------------------------------------
    # 7. Mixed data types
    # --------------------------------------------------

    "Mixed_Data": [
        100,
        "200",
        300,
        "four hundred",
        500,
        None,
        "600",
        700,
        "800",
        900,
        "one thousand",
        1100,
        "1200",
        1300,
        "1400",
    ],


    # --------------------------------------------------
    # 8. Date-like values + invalid dates
    # --------------------------------------------------

    "Date": [
        "2025-01-01",
        "2025-02-01",
        "01/03/2025",
        "2025-04-01",
        "invalid",
        None,
        "2025-06-01",
        "2025-07-01",
        "2025-08-01",
        "2025-09-01",
        "not available",
        "2025-11-01",
        "2025-12-01",
        "01/14/2025",
        "2025-15-01",
    ],


    # --------------------------------------------------
    # 9. Percentage stored as text
    # --------------------------------------------------

    "Conversion_Rate": [
        "10%",
        "20%",
        "15%",
        "25%",
        "30%",
        "5%",
        "12%",
        "18%",
        "22%",
        "8%",
        "14%",
        "16%",
        "20%",
        "11%",
        "9%",
    ],


    # --------------------------------------------------
    # 10. Currency stored as text
    # --------------------------------------------------

    "Revenue": [
        "$1,000",
        "$2,500",
        "$3,200",
        "$4,500",
        "$5,000",
        "$6,000",
        "$7,500",
        "$8,000",
        "$9,500",
        "$10,000",
        "$11,500",
        "$12,000",
        "$13,500",
        "$14,000",
        "$15,000",
    ],


    # --------------------------------------------------
    # 11. Boolean-like values
    # --------------------------------------------------

    "Is_Active": [
        "Yes",
        "No",
        "YES",
        "NO",
        "True",
        "False",
        "true",
        "false",
        "Y",
        "N",
        "yes",
        "no",
        None,
        "Yes",
        "No",
    ],


    # --------------------------------------------------
    # 12. Negative and zero values
    # --------------------------------------------------

    "Profit": [
        1000,
        2500,
        -500,
        3000,
        0,
        4500,
        -1000,
        5000,
        2000,
        -250,
        3500,
        0,
        4200,
        -750,
        6000,
    ],


    # --------------------------------------------------
    # 13. High-cardinality text
    # --------------------------------------------------

    "Email": [
        "alice@example.com",
        "bob@example.com",
        "charlie@example.com",
        "david@example.com",
        "emma@example.com",
        "frank@example.com",
        "george@example.com",
        "hannah@example.com",
        "ian@example.com",
        "jane@example.com",
        "kevin@example.com",
        "lisa@example.com",
        "mike@example.com",
        "nancy@example.com",
        "oliver@example.com",
    ],


    # --------------------------------------------------
    # 14. Free-form text
    # --------------------------------------------------

    "Comments": [
        "Good customer",
        "Very satisfied",
        "Needs improvement",
        "Excellent service",
        "Late payment",
        "",
        "Very satisfied",
        "Good customer",
        "Customer complained",
        "Excellent service",
        "Needs follow-up",
        None,
        "Good customer",
        "Very satisfied",
        "Late payment",
    ],


    # --------------------------------------------------
    # 15. Mostly missing column
    # --------------------------------------------------

    "Optional_Field": [
        None,
        None,
        None,
        "Available",
        None,
        None,
        None,
        None,
        None,
        "Available",
        None,
        None,
        None,
        None,
        None,
    ],


    # --------------------------------------------------
    # 16. Duplicate values
    # --------------------------------------------------

    "Department": [
        "Sales",
        "Sales",
        "HR",
        "IT",
        "Finance",
        "Sales",
        "HR",
        "IT",
        "Finance",
        "Sales",
        "Sales",
        "HR",
        "IT",
        "Finance",
        "Sales",
    ],


    # --------------------------------------------------
    # 17. Numeric values with missing values
    # --------------------------------------------------

    "Experience": [
        1,
        2,
        3,
        None,
        5,
        6,
        7,
        8,
        None,
        10,
        11,
        12,
        13,
        14,
        15,
    ],


    # --------------------------------------------------
    # 18. Text containing whitespace
    # --------------------------------------------------

    "Product": [
        "Laptop",
        "Laptop ",
        " Phone",
        "Tablet",
        "Laptop",
        " Phone ",
        "Monitor",
        "Keyboard",
        "Mouse ",
        "Laptop",
        "Tablet ",
        "Monitor",
        " Keyboard ",
        "Mouse",
        "Phone",
    ],
}

    return pd.DataFrame(data)


if __name__ == "__main__":

    # --------------------------------------------------------
    # Create test dataset
    # --------------------------------------------------------

    df = create_messy_dataset()

    # --------------------------------------------------------
    # Generate dataset profile
    # --------------------------------------------------------

    profile = profile_dataset(df)

    # --------------------------------------------------------
    # Generate preprocessing plan
    # --------------------------------------------------------

    plan = generate_preprocessing_plan(
        profile
    )

    # --------------------------------------------------------
    # Display preprocessing actions
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("PREPROCESSING PLAN")
    print("=" * 70)

    for action in plan.actions:

        print("\nColumn:", action.columns)
        print("Action:", action.action)
        print("Reason:", action.reason)

        if action.parameters:
            print(
                "Parameters:",
                action.parameters
            )

    print("\n")
    print("Reasoning:", plan.reasoning)
    print("Source:", plan.source)