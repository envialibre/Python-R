#pip install scikit-learn
#Este ejercicio busca mostrar cómo entrenar un clasificador de #
#Regresión Logística utilizando el conjunto de datos Iris, que es un conjunto de datos clásico
#en aprendizaje automático utilizado para la clasificación de especies de flores de iris en tres clases


from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Cargar el conjunto de datos Iris
iris = load_iris()
X = iris.data
y = iris.target

# Imprimir la forma inicial de los datos y las primeras muestras
print('Forma inicial de los datos:', X.shape)
print('Primeras 5 muestras:\n', X[:5])
print('Etiquetas:', y[:5])

# Dividir el conjunto de datos en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Inicializar y entrenar un clasificador de Regresión Logística
clf = LogisticRegression()
clf.fit(X_train, y_train)

# Predecir las etiquetas para el conjunto de prueba
y_pred = clf.predict(X_test)

# Evaluar la precisión del clasificador
precision = accuracy_score(y_test, y_pred)

# Verificar si la precisión es considerada buena (para fines de demostración, digamos que precisión >= 0.95 es buena)
if precision >= 0.95:
    print("¡La precisión es buena! Resultados:")
    print("Etiquetas reales:", y_test)
    print("Etiquetas predichas:", y_pred)
    print("Precisión:", precision)
else:
    print("La precisión no es suficientemente buena. Considera mejorar el modelo.")
