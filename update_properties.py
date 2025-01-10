import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

def process_additional_data(file_path, chunksize=50000):
    """Process the second file and update the properties table with enhanced data cleaning"""
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    print(f"Processing file: {file_path}")
    
    # First, let's check what format the account numbers are in the database
    with engine.connect() as connection:
        sample_query = text("""
        SELECT account_number 
        FROM properties 
        LIMIT 5;
        """)
        result = connection.execute(sample_query)
        print("\nSample account numbers from database:")
        db_samples = [row[0] for row in result]
        for acc in db_samples:
            print(f"'{acc}' (length: {len(acc)})")
    
    # Read the file in chunks
    chunks = pd.read_csv(
        file_path,
        sep='\t',
        chunksize=chunksize,
        usecols=['acct', 'accrued_depr_pct', 'qa_cd'],
        dtype={
            'acct': str,
            'accrued_depr_pct': float,
            'qa_cd': str
        },
        encoding='latin1'
    )
    
    total_updates = 0
    
    # Process each chunk
    for chunk_num, chunk in enumerate(tqdm(chunks)):
        # Clean the data
        chunk = chunk.rename(columns={
            'acct': 'account_number',
            'accrued_depr_pct': 'cdu',
            'qa_cd': 'grade'
        })
        
        # Clean account numbers: remove spaces and pad with zeros
        chunk['account_number'] = (chunk['account_number']
                                 .str.strip()  # Remove leading/trailing spaces
                                 .str.replace(r'\s+', '')  # Remove any interior spaces
                                 .str.zfill(13))  # Pad with leading zeros
        
        if chunk_num == 0:
            print("\nSample of processed data after cleaning:")
            sample_data = chunk.head()
            print(sample_data)
            
            # Verify these accounts exist in database
            sample_accounts = tuple(sample_data['account_number'].tolist())
            with engine.connect() as connection:
                verify_query = text("""
                SELECT account_number 
                FROM properties 
                WHERE account_number IN :accounts;
                """)
                result = connection.execute(verify_query, {'accounts': sample_accounts})
                matching_accounts = [row[0] for row in result]
                print("\nMatching accounts found in database:")
                for acc in matching_accounts:
                    print(f"'{acc}' (length: {len(acc)})")
        
        # Batch update using temporary table
        with engine.connect() as connection:
            # Create temporary table
            chunk.to_sql('temp_updates', engine, if_exists='replace', index=False)
            
            # Perform update with detailed debugging
            if chunk_num == 0:
                debug_query = text("""
                SELECT p.account_number as db_account, 
                       t.account_number as update_account,
                       t.cdu, t.grade
                FROM properties p
                JOIN temp_updates t ON p.account_number = t.account_number
                LIMIT 5;
                """)
                result = connection.execute(debug_query)
                print("\nDebug - Matched records:")
                for row in result:
                    print(f"DB Account: '{row[0]}', Update Account: '{row[1]}', CDU: {row[2]}, Grade: {row[3]}")
            
            # Perform the actual update
            update_query = text("""
            WITH updated AS (
                UPDATE properties p
                SET 
                    cdu = t.cdu,
                    grade = t.grade
                FROM temp_updates t
                WHERE p.account_number = t.account_number
                RETURNING 1
            )
            SELECT COUNT(*) as update_count FROM updated;
            """)
            
            result = connection.execute(update_query)
            rows_updated = result.scalar()
            total_updates += rows_updated
            
            connection.commit()
            connection.execute(text("DROP TABLE IF EXISTS temp_updates;"))
            connection.commit()
    
    print(f"\nTotal rows updated: {total_updates}")
    
    # Final verification with sample
    with engine.connect() as connection:
        verify_final = text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(cdu) as rows_with_cdu,
            COUNT(grade) as rows_with_grade
        FROM properties;
        """)
        result = connection.execute(verify_final)
        counts = result.fetchone()
        print(f"\nFinal counts:")
        print(f"Total rows: {counts[0]}")
        print(f"Rows with CDU: {counts[1]}")
        print(f"Rows with grade: {counts[2]}")
        
        # Show some successful updates if any
        sample_query = text("""
        SELECT account_number, cdu, grade 
        FROM properties 
        WHERE cdu IS NOT NULL 
        LIMIT 5;
        """)
        result = connection.execute(sample_query)
        print("\nSample of updated records (if any):")
        for row in result:
            print(row)

if __name__ == "__main__":
    file_path = "/Users/zachdaube/Desktop/python_projects/hcadproject/data/building_res.txt"
    process_additional_data(file_path)