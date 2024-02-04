# Flexible and Synthetic Transplant Kidney Exchange Problem (FASTKEP) Data Generator

## Overview
Flexible and Synthetic Transplant Kidney Exchange Problem (FASTKEP) Data Generator is a repository which implements the kidney exchange data generator first proposed by Saidman et al. [1]. As a starting point, this work draws upon the Java implementation of Dickerson, Procaccia, & Sandholm [2]. Please find this implementation located at https://github.com/JohnDickerson/KidneyExchange/tree/master. An initial translation into Python was completed using [3].


## How to use FASTKEP

First, import the SaidmanGenerator function into the current python file (see below).

```python
from saidman_generator import SaidmanPoolGenerator
```

Next, simply type in the number of PDPs and the number of NDDs desired.

```python
num_pdps = 512
num_ndds = 25
```

Finally, execute the below line of code. Thats it! The compatibility edge matrix and weighting edge matrix will be returned. As well, the features that determined these matrices (e.g., the blood type of the donors and patients and the patient's cPRA attributes) will be provided.
```python
edges, edge_weighting, blood_type_donor, blood_type_patient, blood_cpra = SaidmanPoolGenerator.get_pool_data_synthetic(num_pdps, num_ndds)
```

For any issues please contact can1767@rit.edu

## Note 
Please cite one the authors' recent works if you choose to use this code repository.

## References
[1] S. L. Saidman, A. E. Roth, T. Sönmez, M. U. Ünver, and F. L. Delmonico, “Increasing the opportunity of live kidney donation by matching for two- and three-way exchanges,” Transplantation, vol. 81, no. 5, pp. 773–782, Mar. 2006, doi: 10.1097/01.tp.0000195775.77081.25.<br />
[2] J. P. Dickerson, A. D. Procaccia, and T. Sandholm, “Price of Fairness in Kidney Exchange.” [Online]. Available: www.ifaamas.org<br />
[3] OpenAI, “ChatGPT: OpenAI’s GPT-3-Based Language Model.” 2021.