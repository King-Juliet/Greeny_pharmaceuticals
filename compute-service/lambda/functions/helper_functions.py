#import library
import re

#function to check regex pattern

def check_and_replace_regex(df, column_name, regex_pattern, replacement_value):
    """
    Checks if values in a DataFrame column match a regex pattern. Replaces non-matching values.
    
    Parameters:
    - df (pd.DataFrame): The DataFrame to process.
    - column_name (str): The name of the column to check.
    - regex_pattern (str): The regex pattern to match values against.
    - replacement_value (str or int): The value to replace non-matching entries with.
    
    Returns:
    - pd.DataFrame: The DataFrame with non-matching values replaced.
    """
    
    # Define a function to check if a value matches the regex pattern
    def match_regex(value):
        if re.fullmatch(regex_pattern, str(value)):
            return value
        else:
            return replacement_value
    
    # Apply the match_regex function to the specified column
    df[column_name] = df[column_name].apply(match_regex)
    
    return df


#function for ensuring values are in list, if not replace with default value specified

def values_checker(df, column_name, allowed_values, replacement_value):
    df[column_name] = df[column_name].apply(lambda x: x if x in allowed_values else replacement_value)
    return df

