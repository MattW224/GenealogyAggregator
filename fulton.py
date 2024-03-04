from core import state_abrv
import pandas
import pdb

def parse_newspaper_information(newspaper_entry):
    # Newspaper name composed location, and actual publication nane. Split the two.
    newspaper_elements = newspaper_entry.split(' ')
    element_length = [len(word) for word in newspaper_elements]
    try:
        # Find *index* of element named '2' -- not the second array element.
        # Also account for cases like below, where 'ST' is mistaken for a state abbreviation.
        state_abbreviation_index = element_length[1:].index(2) + 1
    except ValueError:
        print(f'No probable state abbreviation found for row {newspaper_entry}')
        return None, None

    state_abbreviation = newspaper_elements[state_abbreviation_index].upper()
    try:
        state_name = state_abbreviations[state_abbreviation]
    except KeyError:
        print(f'No state abbreviation found for probable abbreviation {probable_state_abbreviation}')
        return None, None

    newspaper_name = " ".join(newspaper_elements[state_abbreviation_index + 1:])
    newspaper_location = " ".join(newspaper_elements[:state_abbreviation_index]) + f', {state_name}'

    return newspaper_name, newspaper_location

def parse_date_information(year_ranges):
    def expand_year(short_year, last_full_year):
        """Expand a year based on the last seen full year, ensuring chronological consistency."""
        try:
            year_int = int(short_year.strip())
            if year_int < 100:  # assuming it's a two-digit year
                predicted_year = int(str(last_full_year)[:2] + str(year_int))
                return predicted_year if predicted_year >= last_full_year else predicted_year + 100
            return year_int
        except ValueError:
            return last_full_year  # return the last full year if conversion fails

    year_ranges_str = str(year_ranges)

    ranges = year_ranges_str.split(',')
    standardized_ranges = []
    last_full_year = 0

    for range_part in ranges:
        # Splitting by hyphen and space, and filtering out empty strings
        years = [y for y in range_part.replace('-', ' ').split(' ') if y]
        expanded_years = []

        for year in years:
            expanded_year = expand_year(year, last_full_year)
            expanded_years.append(expanded_year)
            last_full_year = expanded_year  # update the last seen full year

        # Add the year or range to the list
        if len(expanded_years) == 1:
            standardized_ranges.append((str(expanded_years[0]), str(expanded_years[0])))
        else:
            standardized_ranges.append((str(expanded_years[0]), str(expanded_years[-1])))

    return standardized_ranges

CATALOG="C:\\Users\\mwhee\\Downloads\\Most current Newspapers held\\Most current Newspapers held.xlsx"

# Invert from {'Alabama': 'AL'} to {'AL': 'Alabama'}
state_abbreviations = {v: k for k, v in state_abrv.items()}
# Add Fulton abbreviations not included in core.py.
state_abbreviations['AU'] = 'Australia'
state_abbreviations['CN'] = 'Connecticut'
state_abbreviations['DL'] = 'Delaware'

df = pandas.read_excel(CATALOG, 'Alphabetic')
for index, row in df.iterrows():

    dates = str(row['Approx Dates']).strip()
    # Ignore newspapers with empty, or invalid dates (e.g. "file not found").
    if not dates or not dates[0].isdigit():
        continue

    name, location = parse_newspaper_information(row['Newspaper'])
    dates = parse_date_information(row['Approx Dates'])