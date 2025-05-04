import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Assuming df is your DataFrame from the notebook
# Example 1: Using iterrows() - most straightforward but can be slower for large DataFrames
def analyze_with_iterrows(df):
    """
    Example of analyzing each row using iterrows()
    """
    results = []
    for index, row in df.iterrows():
        # Calculate percentage of votes for each party in this constituency
        total_votes = row['Votes Casted']
        if total_votes > 0:  # Avoid division by zero
            pap_percentage = row['PAP'] / total_votes * 100
            wp_percentage = row['WP'] / total_votes * 100
            
            # Example analysis: Check if PAP won by a close margin (less than 5%)
            margin = pap_percentage - wp_percentage
            is_close_race = 0 < margin < 5
            
            results.append({
                'Constituency': row['Constituency'],
                'PAP_Percentage': pap_percentage,
                'WP_Percentage': wp_percentage,
                'Margin': margin,
                'Is_Close_Race': is_close_race
            })
    
    return pd.DataFrame(results)

# Example 2: Using apply() - more efficient than iterrows
def analyze_with_apply(df):
    """
    Example of analyzing each row using apply()
    """
    def analyze_row(row):
        total_votes = row['Votes Casted']
        if total_votes == 0:
            return pd.Series({
                'Turnout_Percentage': 0,
                'PAP_Vote_Share': 0,
                'Opposition_Combined': 0
            })
        
        # Calculate turnout percentage
        turnout = total_votes / row['Number of Electors'] * 100
        
        # Calculate PAP vote share
        pap_share = row['PAP'] / total_votes * 100
        
        # Calculate combined opposition vote share
        opposition_parties = ['WP', 'SDP', 'PPP', 'SUP', 'PSP', 'SPP', 'RDU', 'PAR', 'SDA', 'NSP', 'IND']
        opposition_votes = sum(row[party] for party in opposition_parties)
        opposition_share = opposition_votes / total_votes * 100
        
        return pd.Series({
            'Turnout_Percentage': turnout,
            'PAP_Vote_Share': pap_share,
            'Opposition_Combined': opposition_share
        })
    
    return df.apply(analyze_row, axis=1)

# Example 3: Using vectorized operations - fastest approach
def analyze_vectorized(df):
    """
    Example of analyzing rows using vectorized operations
    """
    # Make sure we're working with a DataFrame that has a unique index
    df_analysis = df.reset_index(drop=True).copy()
    
    # Filter out the total row if it exists
    df_analysis = df_analysis[df_analysis['Constituency'] != 'TOTAL'].copy()
    
    # Calculate turnout percentage for all constituencies at once
    df_analysis['Turnout_Percentage'] = df_analysis['Votes Casted'] / df_analysis['Number of Electors'] * 100
    
    # Calculate PAP vote share
    df_analysis['PAP_Vote_Share'] = df_analysis['PAP'] / df_analysis['Votes Casted'] * 100
    
    # Calculate if the constituency could have flipped with the shortfall votes
    # Assuming all shortfall votes would go to the strongest opposition party
    opposition_parties = ['WP', 'SDP', 'PPP', 'SUP', 'PSP', 'SPP', 'RDU', 'PAR', 'SDA', 'NSP', 'IND']
    
    # Find the strongest opposition party in each constituency
    for party in opposition_parties:
        df_analysis[f'{party}_Share'] = df_analysis[party] / df_analysis['Votes Casted'] * 100
    
    # Get the maximum opposition vote share for each row
    share_columns = [f'{party}_Share' for party in opposition_parties]
    df_analysis['Max_Opposition_Share'] = df_analysis[share_columns].max(axis=1)
    
    # Handle potential ties in a safer way
    max_party_indices = df_analysis[share_columns].apply(lambda x: x.idxmax(), axis=1)
    df_analysis['Max_Opposition_Party'] = max_party_indices.str.replace('_Share', '')
    
    # Create a new column with the votes for the max opposition party
    # We need to extract the party name and then get the votes for that party
    def get_max_opp_votes(row):
        party = row['Max_Opposition_Party']
        return row[party] if party in opposition_parties else 0
    
    df_analysis['Max_Opposition_Votes'] = df_analysis.apply(get_max_opp_votes, axis=1)
    
    # Check if the constituency could flip if all shortfall votes went to opposition
    df_analysis['Could_Flip'] = (df_analysis['PAP'] - df_analysis['Max_Opposition_Votes']) < df_analysis['Votes Shortfall']
    
    return df_analysis

# Example 4: Using a custom function with lambda
def analyze_with_lambda(df):
    """
    Example of using lambda with apply for simple calculations
    """
    # Calculate winning margin for each constituency
    winning_margin = df.apply(lambda row: 
        (row['PAP'] - max([row[party] for party in ['WP', 'SDP', 'PPP', 'SUP', 'PSP', 'SPP', 'RDU', 'PAR', 'SDA', 'NSP', 'IND'] if row[party] > 0])) 
        if row['Votes Casted'] > 0 else 0, 
        axis=1
    )
    
    # Calculate winning percentage
    winning_percentage = df.apply(lambda row: 
        (winning_margin[row.name] / row['Votes Casted'] * 100) if row['Votes Casted'] > 0 else 0, 
        axis=1
    )
    
    return pd.DataFrame({
        'Constituency': df['Constituency'],
        'Winning_Margin': winning_margin,
        'Winning_Percentage': winning_percentage
    })

# Example 5: Using groupby for analysis by groups
def analyze_by_groups(df):
    """
    Example of grouping and analyzing
    """
    # Create a new column to categorize constituencies by size
    df_with_size = df.copy()
    df_with_size['Size_Category'] = pd.cut(
        df_with_size['Number of Electors'], 
        bins=[0, 20000, 40000, 60000, 100000, float('inf')],
        labels=['Very Small', 'Small', 'Medium', 'Large', 'Very Large']
    )
    
    # Group by size category and calculate average PAP vote share
    size_analysis = df_with_size.groupby('Size_Category').apply(
        lambda group: pd.Series({
            'Avg_PAP_Share': (group['PAP'] / group['Votes Casted'] * 100).mean(),
            'Avg_Turnout': (group['Votes Casted'] / group['Number of Electors'] * 100).mean(),
            'Count': len(group)
        })
    )
    
    return size_analysis

# Example usage:
if __name__ == "__main__":
    # Load your data
    df = pd.read_csv('./out/constituency_electors.csv')
    
    # Remove the TOTAL row for analysis
    df = df[df['Constituency'] != 'TOTAL']
    
    # Run the different analysis methods
    iterrows_results = analyze_with_iterrows(df)
    apply_results = analyze_with_apply(df)
    vectorized_results = analyze_vectorized(df)
    lambda_results = analyze_with_lambda(df)
    group_results = analyze_by_groups(df)
    
    # Print some results
    print("Close races (margin < 5%):")
    print(iterrows_results[iterrows_results['Is_Close_Race']])
    
    print("\nConstituencies that could flip with shortfall votes:")
    print(vectorized_results[vectorized_results['Could_Flip']][['Constituency', 'PAP_Vote_Share', 'Max_Opposition_Share', 'Max_Opposition_Party']])
    
    print("\nAverage PAP performance by constituency size:")
    print(group_results)
