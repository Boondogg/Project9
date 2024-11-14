from flask import Flask, request, render_template, redirect, url_for
import logging
import pandas as pd
import numpy as np

# Changes pandas display settings
pd.options.display.width = None
pd.options.display.max_columns = None
pd.set_option('display.max_rows', 3000)
pd.set_option('display.max_columns', 3000)

# Define allowed files
ALLOWED_EXTENSIONS = {'txt'}
searchList = ["SPLASHES", "GRAZES", "attacks", "CRITICALS", 'DRAINS', 'RAMS', "GRAPPLES", "HACKS", "TAUNTS", "DEFLECTS"]
attack_types = ['GRAZES', 'attacks', 'CRITICALS', 'SPLASHES']
# shipnames = ['Emp-1','Emp-2','Emp-3', 'Emp-4', 'Emp-5', 'Emp-6', 'Emp-7', "Boondog's Het Stinger-I", "Boondog's Striker Gunboat-IV-ULT"]
#colours=['blue','orange','green','red','purple','brown','pink','gray','olive','cyan']
colours=['LightYellow','PapayaWhip','Moccasin','PaleGoldenrod','Khaki','Lavender','LightCyan','PaleTurquoise','LightBlue','Cornsilk']
shipnames = []

def clean_data(df):
    for col in df.columns:
        df[col] = df[col].str.replace('[', '')
        df[col] = df[col].str.replace(']', '')
        df[col] = df[col].str.replace('(', '')
        df[col] = df[col].str.replace(')', '')
        df[col] = df[col].str.replace(r'<.*?>', '', regex=True)

    pattern = '|'.join(searchList)
    df['Ship'] = df['Heading1'].str.split(f'({pattern})').str[0]
    df["Att_Type"] = df['Heading1'].str.extract(f'({pattern})', expand=False)
    df["Att_Type"] = df["Att_Type"].fillna('')

    # List of word pairs to search for
    word_pairs = [
        ('HACKS', 'for'),
        ('TAUNTS', 'for'),
        ('GRAPPLES', 'for'),
        ('DRAINS', 'of'),
        ('RAMS', 'for')
    ]

    # Initialize the 'OtherAtt' column
    df['OtherAtt'] = np.nan
    # Create a regular expression pattern to extract text between the two words
    for word1, word2 in word_pairs:
        pattern = fr'{word1}\s*(.*?)\s*{word2}'
        df['OtherAtt'] = df['OtherAtt'].combine_first(df['Heading1'].str.extract(pattern, expand=False))
        df['OtherAtt'] = df['OtherAtt'].fillna('')

    # Create a regular expression pattern to find numeric values after the specific word
    specific_word = 'for'
    pattern = fr'{specific_word}\s+(\d+)'

    # Extract numeric value directly after the specific word
    df['HullDmg'] = df['Heading1'].str.extract(pattern, expand=False)
    df['HullDmg'] = df['HullDmg'].fillna('0')

    # Create a regular expression pattern to find numeric values after the specific word
    specific_word = 'and'
    pattern = fr'{specific_word}\s+(\d+)'

    # Extract numeric value directly after the specific word
    df['ShieldDmg'] = df['Heading1'].str.extract(pattern, expand=False)
    df['ShieldDmg'] = df['ShieldDmg'].fillna('0')

    df['TotalDmg'] = pd.to_numeric(df['HullDmg']) + pd.to_numeric(df['ShieldDmg'])
    df['TotalDmg'] = df['TotalDmg'].fillna('')

    # Define the two words to search between
    word1 = 'with'
    word2 = 'for'
    # Create a regular expression pattern to extract text between the two words
    pattern = fr'{word1}\s*(.*?)\s*{word2}'
    df['Weapon'] = df['Heading1'].str.extract(pattern, expand=False)
    df['Weapon'] = df['Weapon'].fillna('')

    df['ID'] = range(len(df))

    return df

def calc_stats(df, shipnames):
    df.drop(columns=df.columns[0], axis=1, errors='ignore', inplace=True)
    headers = ['Ship', "Att_Type", 'OtherAtt', 'HullDmg', 'ShieldDmg', 'TotalDmg', 'Weapon', 'ID']
    df = pd.DataFrame(df, columns=headers)
    df = df.drop(columns=['HullDmg', 'ShieldDmg', 'OtherAtt'])

    # Iterate through the DataFrame rows
    for i in range(len(df)):

        if df["Att_Type"].iloc[i] == 'SPLASHES':
            # df.at[i, 'splash_check'] = 'Yes'
            if df.iloc[i]['Ship'] == df.iloc[i - 1]['Ship']:
                # df.at[i, 'splash_check2'] = 'Yes'
                df.at[i, 'Weapon'] = df.iloc[i - 1]['Weapon']

    df = df[~df["Ship"].str.contains("DESTROYED", case=False, na=False)]
    df = df[~df["Ship"].str.contains("wormhole", case=False, na=False)]
    df = df[~df["Ship"].str.contains("XP", case=False, na=False)]
    df = df[~df["Ship"].str.contains("RAMMED", case=False, na=False)]
    df = df[~df["Ship"].str.contains("DRAGGED", case=False, na=False)]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

    df =df[df['Weapon'].str.len() > 0]

    # =================================================
    # Convert DataFrame to List of Lists
    list_of_lists = df.values.tolist()

    # Write the List of Lists to a .py File
    with open('ListofLists.py', 'w') as file:
        file.write('list_of_lists = ' + str(list_of_lists))


    # ================================================
    # ================================================
    # Copy DataFrame
    df_copy = df.copy()

    # Write the copied DataFrame to a .py file
    with open('CopiedDataFrame.py', 'w') as file:
        file.write("import pandas as pd\n\n")
        file.write("data = [\n")
        for row in df_copy.values.tolist():
            file.write(f"    {row},\n")
        file.write("]\n\n")
        file.write("headers = ['Ship', 'Att_Type', 'TotalDmg', 'Weapon']\n\n")
        file.write("df_copy = pd.DataFrame(data, columns=headers)\n")


    # ================================================
    # Initialize a list to store results for all ships
    df2 = df
    all_ships_results = []
    #print('print 3.2')
    print(df)
    for Ship1 in shipnames:
        # Filter the DataFrame for the current ship and remove rows with blank 'Weapon' values
        filtered_df = df[(df['Ship'] == Ship1) & df['Weapon'].notna()]
        if filtered_df.empty:
            continue  # Skip the ship if there are no records
        #print(filtered_df)
        # Get unique weapon values, excluding blanks
        unique_values = filtered_df['Weapon'].unique().tolist()
        remove_blanks = [item for item in unique_values if item]

        # Initialize a dictionary to store results for each weapon
        weapon_stats = {}

        # Calculate sum and count for each weapon, separated by attack type
        for weapon in filtered_df['Weapon'].unique():
            stats = {
                'total_dmg': int(filtered_df[filtered_df['Weapon'] == weapon]['TotalDmg'].sum()),
                'count': int(
                    filtered_df[(filtered_df['Weapon'] == weapon) & (filtered_df["Att_Type"] != 'SPLASHES')].shape[0])
            }
            for attack in attack_types:
                filtered_attack_df = filtered_df[
                    (filtered_df['Weapon'] == weapon) & (filtered_df["Att_Type"].str.upper() == attack.upper())]
                total_dmg = int(filtered_attack_df['TotalDmg'].sum())
                count = int(filtered_attack_df.shape[0])
                stats[f'{attack.lower()}_dmg'] = total_dmg
                stats[f'{attack.lower()}_count'] = count
            stats['avg_dmg'] = stats['total_dmg'] // stats['count'] if stats['count'] > 0 else 0
            weapon_stats[weapon] = stats

        # Create a list of results for the current ship
        results_list = [
            [
                Ship1,
                weapon,
                stats['total_dmg'],
                stats['avg_dmg'],
                stats['count'],
                stats.get('grazes_dmg', 0), stats.get('grazes_count', 0),
                stats.get('attacks_dmg', 0), stats.get('attacks_count', 0),
                stats.get('criticals_dmg', 0), stats.get('criticals_count', 0),
                stats.get('splashes_dmg', 0), stats.get('splashes_count', 0)
            ]
            for weapon, stats in weapon_stats.items()
        ]

        all_ships_results.extend(results_list)

    # Create a new DataFrame from the combined results
    columns = ['Ship', 'Weapon', 'Tot_Dmg', 'Tot_Cnt', 'Avg_Dmg',
               'Gz_Dmg', 'Gz_Cnt', 'Att_Dmg', 'Att_Cnt',
               'Crit_Dmg', 'Crit_Cnt', 'Spl_Dmg', 'Spl_Cnt']
    df = pd.DataFrame(all_ships_results, columns=columns)

    for Ship1 in shipnames:
        # Filter the DataFrame for the current ship and remove rows with blank 'Weapon' values
        filtered_df = df2[(df2['Ship'] == Ship1)]
        if filtered_df.empty:
            continue  # Skip the ship if there are no records

        total_damage = filtered_df['TotalDmg'].sum()
        total_count = filtered_df['count'].sum()
        print(f'Total damage for {Ship1}: {total_damage}')
        print(f'Total count for {Ship1}: {total_count}')




    print('print 4')
    print(df)





    return df

app = Flask(__name__)

# Configure upload file path flask
app.secret_key = 'This is your secret key to utilize session in Flask'

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_form1', methods=['POST'])
def submit_form1():
    # Get form data
    form_data = [
        request.form.get('name1'),
        request.form.get('name2'),
        request.form.get('name3'),
        request.form.get('name4'),
        request.form.get('name5'),
        request.form.get('name6'),
        request.form.get('name7'),
        request.form.get('name8'),
        request.form.get('name9'),
        request.form.get('name10')
    ]
    # Store the form data in the list
    shipnames.extend(form_data)

    print(shipnames)
    return redirect(url_for('upload_file'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    app.logger.debug('Upload route accessed')

    if request.method == 'POST':
        # upload file flask
        f = request.files.get('file')

        # Read the file content
        file_content = f.read().decode('utf-8').splitlines()

        if file_content is None:
            return "No file uploaded", 400

        # Create a DataFrame from the lines
        lines = [value for i, value in enumerate(file_content) if i % 2 != 0]
        df = pd.DataFrame(lines, columns=['Heading1'])

        clean_data(df)
        df = calc_stats(df, shipnames)
        # df2 = calc_stats(df, shipnames)

        # Converting to HTML Table
        uploaded_df_html = df.to_html(classes='table table-bordered', index=False)

        return render_template('index4.html', data_var=uploaded_df_html, data=df.values.tolist(),
            shipnames=shipnames, colours=colours, enumerate=enumerate)
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
