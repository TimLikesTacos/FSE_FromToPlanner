import re


def to_snake(before):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', before).lower()


def remove_unnamed_from_df(df):
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

# For pandas dataframe
def change_nan_to_none (df):
    return df.where(df.notnull(), None)