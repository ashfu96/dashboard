import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sklearn
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import f
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

# FUNZIONE LETTURA DATASET
def load_data(data):
    return pd.read_csv(data, delimiter=" ", header=None)

    
# FILTRO DEL DATASET PER UNIT_ID SELEZIONATA
def filter_by_unit(df , selected_unit_id):
    """
    # Creazione del menu sidebar per la selezione dell'unit_id
    """    
    # Filtro del dataframe per la unit_ID selezionata
    filtered_data = df[df['unit_ID'] == selected_unit_id]

    # Restituisce il DataFrame filtrato
    return filtered_data


# CONTEGGIO VOLI EFFETTUATI PER UNIT_ID
def count_cycles_by_unit(df):
    """
    Raggruppa il DataFrame in base all'unit_id e calcola il conteggio dei valori della colonna time_in_cycles per ogni gruppo
    """
    counts = df.groupby('unit_ID')['time_in_cycles'].count()

    # Crea una lista di stringhe di testo che mostrano il conteggio dei time_in_cycles per ogni unit_id
    results = [f"L'unità {unit_id} ha effettuato {count} voli." for unit_id, count in counts.items()]

    # Restituisce la lista di stringhe di testo
    return results


# NORMALIZZAZIONE COLONNE TEST
def normalize_test_columns(df, cols_to_exclude):
    """
    Normalizza le colonne del dataset di test in modo che i valori siano compresi tra 0 e 1 utilizzando il Min-Max Scaler, 
    escludendo le colonne specificate da cols_to_exclude.
    """
    # Crea una copia del DataFrame di test
    df_test = df.copy()
    
    # Crea un oggetto MinMaxScaler
    min_max_scaler = MinMaxScaler()
    
    # Aggiungi una colonna "cycle_norm" con i valori di "time_in_cycles"
    df_test['cycle_norm'] = df_test['time_in_cycles']
    
    # Seleziona le colonne da normalizzare
    cols_to_normalize = df_test.columns.difference(cols_to_exclude + ['unit_ID', 'time_in_cycles'])
    
    # Normalizza le colonne del dataset di test
    norm_test_df = pd.DataFrame(min_max_scaler.fit_transform(df_test[cols_to_normalize]), 
                                columns=cols_to_normalize,
                                index=df_test.index)
    
    # Combina le colonne normalizzate con le colonne escluse dal processo di normalizzazione
    test_join_df = df_test[df_test.columns.difference(cols_to_normalize)].join(norm_test_df)
    
    # Riordina le colonne del DataFrame
    df_test = test_join_df.reindex(columns=df_test.columns)
    
    # Reimposta l'indice delle righe del DataFrame
    df_test.reset_index(drop=True, inplace=True)
    
    return df_test


###############  PLOT SENSORI IMPORTANTI  ###################

# PLOT DEI 4 SENSORI TUTTI INSIEME
def plot_selected_columns(df_train, selected_unit_id, selected_columns):
    # Filter the DataFrame for the selected unit ID
    df_selected_unit = df_train[df_train['unit_ID'] == selected_unit_id]
    
    # Define a list of colors
    colors = ['b', 'g', 'r', 'c']
       
    # Create a figure and a grid of subplots
    fig, axs = plt.subplots(2, 2, figsize=(15, 15))
    # Flatten the array of axes, for easier indexing
    axs = axs.flatten()
    
    # Plot ogni colonns
    for i, column in enumerate(selected_columns):
        axs[i].plot(df_selected_unit[column].values, color=colors[i % len(colors)], label=column)
        axs[i].set_title('Valore del sensore "{}" per l\' unità con ID "{}"'.format(column, selected_unit_id))
        axs[i].set_xlabel('Cicli effettuati')
        axs[i].set_ylabel('Valore')
        axs[i].legend()
    
    # rimozione subplot inutili
    for i in range(4, 4):
        fig.delaxes(axs[i])    
    # evitare sovrapposizioni
    plt.tight_layout()
    st.pyplot(fig)

 
######### SELEZIONE DEL SINGOLO SENSORE DALLA SIDEBAR
def plot_sensor(df, selected_unit_id, selected_column):
    # Filtra il DataFrame del test per l'unità selezionata
    df_selected_unit = df[df['unit_ID'] == selected_unit_id]

    # Visualizza il grafico della colonna selezionata per l'unità selezionata
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.plot(df_selected_unit[selected_column].values, label=selected_column)
    ax.set_title('Valori del sensore "{}" per l\'unità "{}"'.format(selected_column, selected_unit_id))
    ax.set_xlabel('Cicli effettuati')
    ax.set_ylabel('Valore')

    # Utilizza st.pyplot() per visualizzare il grafico all'interno dell'applicazione Streamlit
    st.header(f"Valori del sensore {selected_column} per l\'unità {selected_unit_id}")
    st.pyplot(fig)
    
def plot_hotelling_tsquare(df, selected_unit_id, sensors):

    # Filter data for the specified unit_id
    unit_data = df[df['unit_ID'] == selected_unit_id]

    # Select the variables of interest for the specified unit_id
    unit_data_selected = unit_data[sensors]
    unit_data_selected.reset_index(drop=True, inplace=True)
    
    # Calculate the mean vector for the selected variables
    mean_vector = np.mean(unit_data_selected, axis=0)

    # Calculate the covariance matrix for the selected variables
    covariance_matrix = np.cov(unit_data_selected.values, rowvar=False)

    # Calculate the Hotelling's T-square for each row in the specified unit_id
    unit_T_square = np.dot(np.dot((unit_data_selected - mean_vector), np.linalg.inv(covariance_matrix)), (unit_data_selected - mean_vector).T).diagonal()

    return  unit_T_square


def plot_hotelling_tsquare_comparison(df_train, df_test, selected_unit_id, sensors):
    # Create a figure and axes
    fig, ax = plt.subplots()
    # Plot the Hotelling's T-square for the training data
    unit_T_square_train = plot_hotelling_tsquare(df_train, selected_unit_id, sensors)

    # Plot the Hotelling's T-square for the test data
    unit_T_square_test = plot_hotelling_tsquare(df_test, selected_unit_id, sensors)
    # Plot the Hotelling's T-square for the test data
    unit_T_square_test = plot_hotelling_tsquare(df_test, selected_unit_id, sensors)

    # Plot the Hotelling's T-square values and the critical value
    ax.plot(unit_T_square_train, label="normal data")
    ax.plot(unit_T_square_test, label="actual data")
    ax.set_xlabel('Row Index')
    ax.set_ylabel("Hotelling's T-square")
    ax.set_title(f'Hotelling\'s T-square for Unit ID {selected_unit_id}')
    ax.legend()

    # Display the plot using st.pyplot()
    st.pyplot(fig)

#################################################################################    
#           HEALT-INDEX
#################################################################################

#  SLIDER PER IMPOSTAZIONI AVANZATE
def show_sliders():
    st.write("Modifica i pesi dei sensori:")
    weight1 = st.slider('T30 (w)', min_value=0.0, max_value=1.0, value=0.1, step=0.1)
    weight2 = st.slider('T50 (w) ', min_value=0.0, max_value=1.0, value=0.5, step=0.1)
    weight3 = st.slider('Nc (w)', min_value=0.0, max_value=1.0, value=0.2, step=0.1)
    weight4 = st.slider('NRc (w)', min_value=0.0, max_value=1.0, value=0.8, step=0.1)
    return weight1, weight2, weight3, weight4

def calculate_and_plot_health_index(df, unit_id, weights):
    # Check if weights are valid
    if len(weights) != 4:
        raise ValueError("weights list must have exactly four elements.")

    # Normalize sensor readings for each unit
    df_normalized = df.groupby('unit_ID').transform(lambda x: (x - x.min()) / (x.max() - x.min()))

    # Calculate health index
    df['health_index'] = np.dot(df_normalized[['T30', 'T50', 'Nc', 'NRc']], weights)

    # Filter dataframe for the given unit ID
    df_unit = df[df['unit_ID'] == unit_id]

    # Create a new figure
    plt.figure(figsize=(10, 6))

    # Plot health index for the specified unit
    plt.plot(df_unit.index, df_unit['health_index'], label=f'Unit {unit_id}')

    # Add title and labels
    plt.title(f'Health Index Over Time for Unit nr° {unit_id} (the increasing of the parameters shows off suffering of the engine)')
    plt.xlabel('Time')
    plt.ylabel('Health Index')

    # Add a legend
    plt.legend()
    
    # Show the plot
    st.pyplot()
    
   
def get_last_sequences_with_predictions(df, sequence_cols, sequence_length, model):
    
    unique_unit_ids = df['unit_ID'].unique()
    predictions = []
    
    for unit_id in unique_unit_ids:
        unit_df = df[df['unit_ID'] == unit_id]
        
        if len(unit_df) >= sequence_length:
            sequence = unit_df[sequence_cols].values[-sequence_length:]
            sequence = np.asarray([sequence])
            prediction = model.predict(sequence)[0]
            predictions.append(prediction)
        else:
            predictions.append(np.nan)  # Add NaN for missing predictions
    
    predictions = np.asarray(predictions)
    result_df = pd.DataFrame({'unit_ID': unique_unit_ids, 'prediction': predictions})
    return result_df
