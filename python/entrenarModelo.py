import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import numpy as np

# PASO 1: Cargar los datos
# Simulación de la carga de datos - en un caso real se cargaría un archivo CSV o una base de datos
# Suponiendo que tenemos las siguientes columnas: 'hora_del_dia', 'dia_de_la_semana', y 'tiempo_entre_estaciones'
datos = pd.DataFrame({
    'hora_del_dia': np.random.choice(range(24), size=100),
    'dia_de_la_semana': np.random.choice(range(7), size=100),
    'condiciones_meteorologicas': np.random.choice(['soleado', 'lluvioso', 'nublado'], size=100),
    'tiempo_entre_estaciones': np.random.normal(loc=10, scale=2, size=100)  # supongamos una distribución normal con media 10 y desviación estándar 2
})

# Convertir las condiciones meteorológicas en variables dummies para el análisis
datos = pd.get_dummies(datos, columns=['condiciones_meteorologicas'], drop_first=True)

# PASO 2: Preparar los datos para el entrenamiento del modelo
# Separar las características (X) de la etiqueta (y) que queremos predecir
X = datos.drop('tiempo_entre_estaciones', axis=1)
y = datos['tiempo_entre_estaciones']

# Dividir los datos en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# PASO 3: Crear y entrenar el modelo de aprendizaje automático
# Instanciar el modelo de Random Forest
modelo = RandomForestRegressor(n_estimators=100, random_state=42)

# Entrenar el modelo con los datos de entrenamiento
modelo.fit(X_train, y_train)

# PASO 4: Evaluar el modelo
# Predecir los tiempos de viaje en el conjunto de prueba
predicciones = modelo.predict(X_test)

# Calcular el error cuadrático medio (MSE) como medida de la precisión del modelo
error = mean_squared_error(y_test, predicciones)
print(f"El error cuadrático medio (MSE) del modelo es: {error}")

# PASO 5: Utilizar el modelo para realizar predicciones en tiempo real
def predecir_tiempo_de_viaje(hora, dia, condiciones):
    # Crear un dataframe con todas las posibles condiciones meteorológicas
    # y establecerlas a 0 (cero)
    caracteristicas = pd.DataFrame({
        'hora_del_dia': [hora],
        'dia_de_la_semana': [dia],
        'condiciones_meteorologicas_soleado': 0,
        'condiciones_meteorologicas_lluvioso': 0,
        'condiciones_meteorologicas_nublado': 0
    })
    
    # Establecer la característica correspondiente a 1 según la condición meteorológica proporcionada
    if condiciones in caracteristicas:
        caracteristicas[f'condiciones_meteorologicas_{condiciones}'] = 1
    
    # Se asegúra que el orden de las columnas coincida con el orden de entrenamiento del modelo
    caracteristicas = caracteristicas.reindex(columns=modelo.feature_names_in_, fill_value=0)
    
    # Realizar la predicción utilizando el modelo
    tiempo_estimado = modelo.predict(caracteristicas)[0]
    return tiempo_estimado


# Ejemplo de uso de la función de predicción
tiempo_estimado = predecir_tiempo_de_viaje(14, 3, 'soleado')
print(f"El tiempo estimado de viaje es: {tiempo_estimado} minutos")
