import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from tqdm import tqdm
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_numeric(value):
    """Clean numeric values, handling empty strings and invalid numbers"""
    if pd.isna(value) or value == '' or value.strip() == '':
        return None
    try:
        return float(str(value).replace(',', ''))
    except:
        return None

def process_hcad_file(file_path, chunksize=10000):
    """Process HCAD property data file and load into PostgreSQL"""
    
    # Get database URL from environment variable
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    # Column mapping based on HCAD file structure
    column_mapping = {
        'acct': 'account_number',
        'site_addr_1': 'street_address',
        'site_addr_2': 'city',
        'site_addr_3': 'zip_code',
        'Neighborhood_Code': 'neighborhood_code',
        'Market_Area_1': 'market_area',
        'Market_Area_1_Dscr': 'market_description',
        'yr_impr': 'year_built',
        'bld_ar': 'building_area',
        'land_ar': 'land_area',
        'acreage': 'acreage',
        'land_val': 'land_value',
        'bld_val': 'building_value',
        'x_features_val': 'extra_features_value',
        'tot_appr_val': 'total_appraised_value',
        'tot_mkt_val': 'total_market_value'
    }
    
    print(f"Processing file: {file_path}")
    print("Reading data in chunks...")
    
    # Try different encodings
    encodings = ['latin1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            print(f"Trying encoding: {encoding}")
            # Read and process the file in chunks
            chunks = pd.read_csv(
                file_path,
                sep='\t',
                chunksize=chunksize,
                usecols=column_mapping.keys(),
                dtype=str,  # Read everything as string initially
                encoding=encoding,  # Specify encoding
                on_bad_lines='skip'  # Skip problematic lines
            )
            
            # If we get here, the encoding worked
            print(f"Successfully opened file with {encoding} encoding")
            
            # Process each chunk
            for i, chunk in enumerate(tqdm(chunks)):
                # Rename columns
                chunk = chunk.rename(columns=column_mapping)
                
                # Clean numeric columns
                numeric_columns = ['building_area', 'land_area', 'acreage', 'land_value', 
                                'building_value', 'extra_features_value', 'total_appraised_value', 
                                'total_market_value']
                
                for col in numeric_columns:
                    chunk[col] = chunk[col].apply(clean_numeric)
                
                # Clean year_built
                chunk['year_built'] = pd.to_numeric(chunk['year_built'], errors='coerce')
                
                # Strip whitespace from string columns
                string_columns = ['account_number', 'street_address', 'city', 'zip_code', 
                                'neighborhood_code', 'market_area', 'market_description']
                for col in string_columns:
                    chunk[col] = chunk[col].str.strip()
                
                # Write to database
                try:
                    chunk.to_sql(
                        'properties',
                        engine,
                        if_exists='append' if i > 0 else 'replace',
                        index=False,
                        method='multi'
                    )
                    print(f"Processed chunk {i+1}")
                except Exception as e:
                    print(f"Error processing chunk {i+1}: {str(e)}")
                    continue
            
            # If we successfully processed the file, break the encoding loop
            break
            
        except UnicodeDecodeError:
            print(f"Encoding {encoding} failed, trying next encoding...")
            continue
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise

if __name__ == "__main__":
    # Update this path to where your HCAD data file is located
    file_path = "/Users/zachdaube/Desktop/python_projects/hcadproject/data/real_acct.txt"  # Update this!
    process_hcad_file(file_path)