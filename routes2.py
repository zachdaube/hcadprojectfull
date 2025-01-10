from fastapi import APIRouter, HTTPException, Depends
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from decimal import Decimal

# Load environment variables
load_dotenv()

MINIMUM_COMPS = 5

# Initial range params
INITIAL_PARAMS = {
    'YEAR_DIFFERENCE': 3,  # ±3 years
    'BUILDING_AREA_PERCENTAGE': 10,  # ±10%
    'LAND_AREA_PERCENTAGE': 10,  # ±10%
    'CDU_DIFFERENCE': 0.1  # ±0.1
}

# Expanded range params
EXPANDED_PARAMS = [
    #First expansion: wider year range
    {
        'YEAR_DIFFERENCE': 6,  # ±6 years
        'BUILDING_AREA_PERCENTAGE': 10,  # ±10%
        'LAND_AREA_PERCENTAGE': 10,  # ±10%
        'CDU_DIFFERENCE': 0.1  # ±0.1
    },
    #Second expansion: wider year range and wider cdu range
    {
        'YEAR_DIFFERENCE': 6,  # ±6 years
        'BUILDING_AREA_PERCENTAGE': 10,  # ±10%
        'LAND_AREA_PERCENTAGE': 10,  # ±10%
        'CDU_DIFFERENCE': 0.2  # ±0.2
    },
    #Third expansion: wider year range cdu range and land/building area range
    {
        'YEAR_DIFFERENCE': 6,  # ±6 years
        'BUILDING_AREA_PERCENTAGE': 20,  # ±20%
        'LAND_AREA_PERCENTAGE': 20,  # ±20%
        'CDU_DIFFERENCE': 0.2  # ±0.2
    }
]

# Create router object for API endpoints
router = APIRouter()


def get_db_connection():
    #Create a database connection
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def convert_to_float(value):
    #Convert your value to a float, return None if not possible
    if value is None:
        return None
    try:
        return float(value)
    except:
        return None

def calculate_ranges(property_data, params):
    #Calculate neccessary ranges for property based on given parameters
    
    #Calculate year range
    if not property_data['year_built']:
        year_range = {'min': 0, 'max': 9999}
    else:
        year_range = {
            'min': property_data['year_built'] - params['YEAR_DIFFERENCE'],
            'max': property_data['year_built'] + params['YEAR_DIFFERENCE']
        }

    #Calculate building area range
    building_area = convert_to_float(property_data['building_area'])
    
    if building_area:
        
        building_percentage = params['BUILDING_AREA_PERCENTAGE'] / 100
        building_range = {
            'min': building_area * (1 - building_percentage),
            'max': building_area * (1 + building_percentage)
        }
    else:
        building_range = {'min': 0, 'max': float('inf')}

    #Calculate land area range
    land_area = convert_to_float(property_data['land_area'])
    
    if land_area:
        land_percentage = params['LAND_AREA_PERCENTAGE'] / 100
        land_range = {
            'min': land_area * (1 - land_percentage),
            'max': land_area * (1 + land_percentage)
        }
    else:
        land_range = {'min': 0, 'max': float('inf')}

    #Calculate cdu range
    cdu = convert_to_float(property_data['cdu'])
    if cdu:
        cdu_range = {
            'min': max(0, cdu - params['CDU_DIFFERENCE']),
            'max': min(1, cdu + params['CDU_DIFFERENCE'])
        }
    else:
        cdu_range = {'min': 0, 'max': float('inf')}

    #Return dictionary of corresponding ranges
    return {
        'year_range': year_range,
        'building_area_range': building_range,
        'land_area_range': land_range,
        'cdu_range': cdu_range
    }


def get_property_by_account(account_number):
    #Retrieve property by its account number. Returns the property data as a dictionary with column name as key and value as value
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT *
            FROM properties
            WHERE account_number = %s;
            """
            cursor.execute(query, (account_number,))
            property_data  = cursor.fetchone()
            conn.close()
            return property_data
    except Exception as e:
        print(f'Error getting property: {e}')
        return None
    
def find_comparable_properties(property_data, ranges):
    #Returns dictionary of comparable properties to input property data matching the required parameters and ranges
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT *
            FROM properties
            WHERE neighborhood_code = %s
            AND grade = %s
            AND year_built BETWEEN %s AND %s
            AND building_area BETWEEN %s AND %s
            AND land_area BETWEEN %s AND %s
            AND cdu BETWEEN %s AND %s
            AND account_number != %s;
            """
            cursor.execute(query, (
                property_data['neighborhood_code'], 
                property_data['grade'], 
                ranges['year_range']['min'],
                ranges['year_range']['max'],
                ranges['building_area_range']['min'],
                ranges['building_area_range']['max'],
                ranges['land_area_range']['min'],
                ranges['land_area_range']['max'],
                ranges['cdu_range']['min'],
                ranges['cdu_range']['max'],
                property_data['account_number']
            ))
            comparable_properties = cursor.fetchall()
            conn.close()
            return comparable_properties
        
    except Exception as e:
        print(f'Error finding properties: {e}')
        return None

def find_comps_expanded_params(reference_property):
    #Find comparables with progressively wider criteria until minimum count is met

    ranges = calculate_ranges(reference_property, INITIAL_PARAMS)
    comps = find_comparable_properties(reference_property, ranges)

    if comps and len(comps) >= MINIMUM_COMPS:
        return comps, ranges, "initial"
    
    for i, params in enumerate(EXPANDED_PARAMS, 1):
        ranges = calculate_ranges(reference_property, params)
        comps = find_comparable_properties(reference_property, ranges)
        
        if comps and len(comps) >= MINIMUM_COMPS:
            return comps, ranges, f"expansion_{i}"
    
    if comps:
        return comps, ranges, "final_expansion"
    
    return None, None, None
    
def calculate_adjusted_values(reference_property, comparable_properties):

    comp_calculations = []

    for comp in comparable_properties:

        try:
            # Convert values to Decimal for consistent calculations
            building_value = Decimal(str(comp['building_value']))
            extra_features = Decimal(str(comp['extra_features_value'] or 0))
            ref_cdu = Decimal(str(reference_property['cdu']))
            comp_cdu = Decimal(str(comp['cdu'])) if comp['cdu'] != 0 else Decimal('1')
            building_area = Decimal(str(comp['building_area'])) if comp['building_area'] != 0 else Decimal('1')

            # 1. Subtract extra features from building value
            adjusted_building_value = building_value - extra_features
            
            # 2. Apply CDU factor adjustment
            cdu_factor = ref_cdu / comp_cdu
            cdu_adjusted_value = adjusted_building_value * cdu_factor
            
            # 3. Calculate price per square foot
            price_per_sqft = cdu_adjusted_value / building_area
            
            # Convert back to float for JSON serialization
            comp_calculations.append({
                'account_number': comp['account_number'],
                'street_address': comp['street_address'],
                'original_value': float(building_value),
                'adjusted_building_value': float(adjusted_building_value),
                'cdu_factor': float(cdu_factor),
                'cdu_adjusted_value': float(cdu_adjusted_value),
                'price_per_sqft': float(price_per_sqft)
            })
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(f"Error processing comparable {comp['account_number']}: {e}")
            continue
    
    sorted_calcs = sorted(comp_calculations, key=lambda x: x['price_per_sqft'])

    lowest_five = sorted_calcs[:min(5, len(sorted_calcs))]

    prices_per_sqft = [calc['price_per_sqft'] for calc in lowest_five]
    median_price_per_sqft = sorted(prices_per_sqft)[len(prices_per_sqft) // 2]

    building_value = median_price_per_sqft * reference_property['building_area']
    final_adjusted_value = (
        building_value +
        reference_property['land_value'] +
        reference_property['extra_features_value']
    )

    return {
        'lowest_five_comps': lowest_five,
        'median_price_per_sqft': median_price_per_sqft,
        'final_adjusted_value': final_adjusted_value,
        'value_breakdown': {
            'building_value': building_value,
            'land_value': reference_property['land_value'],
            'extra_features_value': reference_property['extra_features_value']
        }
    }



#Get a property and find its comparables
@router.get("/api/property/{account_number}")
async def get_property_analysis(account_number: str):

    reference_property = get_property_by_account(account_number)
    if not reference_property:
        raise HTTPException (
            status_code=404, 
            detail = f"Property with account number {account_number} not found"
        )
    
    comps, ranges, expansion_level = find_comps_expanded_params(reference_property)

    if not comps:
        raise HTTPException(
            status_code=404,
            detail="No comparable properties found"
        )
    
    value_analysis = calculate_adjusted_values(reference_property, comps)
    
    response = {
        'reference_property': reference_property,
        'comparable_properties': comps,
        'num_comps_found': len(comps),
        #'search_expansion_level': expansion_level,
        'value_analysis': value_analysis
    }

    return response


def search_properties_by_address(address_query):
    """Finds properties based on its street address"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            SELECT *
            FROM properties
            WHERE UPPER(street_address) LIKE UPPER(%s)
            ORDER BY street_address
            LIMIT 10;
            """
            search_pattern = f"%{address_query.strip().upper()}%"
            cursor.execute(query, (search_pattern,))
            
            properties = cursor.fetchall()
            
            conn.close()
            return properties
    except Exception as e:
        print(f"Error searching properties: {e}")
        return None

@router.get("/api/search")
async def search_properties(query: str):
    """Search for properties by street address"""
    properties = search_properties_by_address(query)
    
    if properties is None:
        raise HTTPException(
            status_code=500,
            detail="Error occurred while searching properties"
        )
        
    if not properties:
        raise HTTPException(
            status_code=404,
            detail=f"No properties found matching '{query}'"
        )
        
    return properties