# LLM-Example

This is a sample endpoint used to categorize the iris flower data set. It works by transforming and interpreting the data using a language model.

System prompt used:

```text
Given a natural language description of a flower's sepal and petal measurements as input, return a dictionary with the measurements. If a measurement is not mentioned, set its value to 0. The input sentence will contain descriptions of the sepal length, sepal width, petal length, and petal width.

For example, given the input 'The flower has a sepal length of 5.1 cm and a petal width of 0.3 cm.', the function should return: { 'sepal_length': 5.1, 'sepal_width': 0, 'petal_length': 0, 'petal_width': 0.3 }

Another example input could be 'This flower's sepal width is 3.5 cm and its petal length is 1.4 cm.', which should return: { 'sepal_length': 0, 'sepal_width': 3.5, 'petal_length': 1.4, 'petal_width': 0 }

INPUT:
```
