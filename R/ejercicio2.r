#install.packages("caret")
#Este ejercicio se utiliza caret para simplificar el proceso de entrenamiento de 
#modelos de aprendizaje automático en R.
#busca entrenar un modelo de clasificación que pueda
#predecir la especie de una flor de iris (setosa, versicolor o virginica) 
#basándose en las medidas del sépalo y el pétalo. Utiliza el conjunto de datos Iris, 
#que es un conjunto de datos clásico en la ciencia de datos y se encuentra disponible en R


# Cargar la biblioteca caret
library(caret)

# Cargar el conjunto de datos Iris
data("iris")

# Dividir el conjunto de datos en conjuntos de entrenamiento y prueba
set.seed(123) # Para reproducibilidad
trainIndex <- createDataPartition(iris$Species, p = 0.8, list = FALSE)
trainData <- iris[trainIndex, ]
testData <- iris[-trainIndex, ]

# Entrenar un modelo de clasificación utilizando árboles de decisión
model <- train(Species ~ ., data = trainData, method = "rpart")

# Visualizar el modelo
print(model)

# Evaluar el rendimiento del modelo en el conjunto de prueba
predictions <- predict(model, testData)
confusionMatrix(predictions, testData$Species)

