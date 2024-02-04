# author: Calvin Nau
# Date: 10/05/2023

# original procedure from: "Roth, A. E., Sönmez, T., Ünver, M. U., Delmonico, F. L., & Saidman, S. L. (2006). 
# Utilizing list exchange and nondirected donation through ‘chain’paired kidney donations. American Journal of 
# transplantation, 6(11), 2694-2705."
# Code adapted from Java implementation of https://github.com/JohnDickerson/KidneyExchange/tree/master using 
# https://chat.openai.com/
# https://chat.openai.com/share/5340f458-6150-43ef-830c-b5281b389bf8

import torch
import numpy as np
np.random.seed(34252) 

class BloodType:
    O = "O"
    A = "A"
    B = "B"
    AB = "AB"

class VertexPair:
    def __init__(self, ID, bloodTypePatient, bloodTypeDonor, isWifePatient, patientCPRA, compatible):
        self.ID = ID
        self.bloodTypePatient = bloodTypePatient
        self.bloodTypeDonor = bloodTypeDonor
        self.isWifePatient = isWifePatient
        self.patientCPRA = patientCPRA
        self.compatible = compatible

class VertexAltruist:
    def __init__(self, ID, bloodTypeDonor):
        self.ID = ID
        self.bloodTypeDonor = bloodTypeDonor

class Pool:
    def __init__(self):
        self.pairs = []
        self.altruists = []
        self.edges = []
        self.edges_ids = []

    def addPair(self, pair):
        self.pairs.append(pair)

    def addAltruist(self, altruist):
        self.altruists.append(altruist)

    def addEdge(self, source, target):
        self.edges.append((source, target))
        self.edges_ids.append((source.ID, target.ID))


class SaidmanPoolGenerator:
    # Constants validated
    Pr_FEMALE = 0.4090

    Pr_SPOUSAL_DONOR = 0.4897

    Pr_LOW_PRA = 0.7019
    Pr_MED_PRA = 0.2

    Pr_LOW_PRA_INCOMPATIBILITY = 0.05
    Pr_MED_PRA_INCOMPATIBILITY = 0.45
    Pr_HIGH_PRA_INCOMPATIBILITY = 0.90

    Pr_SPOUSAL_PRA_COMPATIBILITY = 0.75

    Pr_PATIENT_TYPE_O = 0.4814
    Pr_PATIENT_TYPE_A = 0.3373
    Pr_PATIENT_TYPE_B = 0.1428

    Pr_DONOR_TYPE_O = 0.4814
    Pr_DONOR_TYPE_A = 0.3373
    Pr_DONOR_TYPE_B = 0.1428

    currentVertexID = 0

    def __init__(self):
        pass

    def get_random_val(self):
        return np.random.random()
        
    def drawPatientBloodType(self):
        r = self.get_random_val()

        if r <= self.Pr_PATIENT_TYPE_O: 
            return BloodType.O
        if r <= self.Pr_PATIENT_TYPE_O + self.Pr_PATIENT_TYPE_A: 
            return BloodType.A
        if r <= self.Pr_PATIENT_TYPE_O + self.Pr_PATIENT_TYPE_A + self.Pr_PATIENT_TYPE_B: 
            return BloodType.B
        return BloodType.AB

    def drawDonorBloodType(self):
        r = self.get_random_val()
        
        if r <= self.Pr_DONOR_TYPE_O: 
            return BloodType.O
        if r <= self.Pr_DONOR_TYPE_O + self.Pr_DONOR_TYPE_A: 
            return BloodType.A
        if r <= self.Pr_DONOR_TYPE_O + self.Pr_DONOR_TYPE_A + self.Pr_DONOR_TYPE_B: 
            return BloodType.B
        return BloodType.AB
    
    def isPatientFemale(self):
        return self.get_random_val() <= self.Pr_FEMALE
    
    def isDonorSpouse(self):
        return self.get_random_val() <= self.Pr_SPOUSAL_DONOR

    def isPositiveCrossmatch(self, pr_PraIncompatibility):
        return self.get_random_val() <= pr_PraIncompatibility

    def generatePraIncompatibility(self, isWifePatient):
        r = self.get_random_val()
        if r <= self.Pr_LOW_PRA:
            pr_PraIncompatibility = self.Pr_LOW_PRA_INCOMPATIBILITY
        elif r <= self.Pr_LOW_PRA + self.Pr_MED_PRA:
            pr_PraIncompatibility = self.Pr_MED_PRA_INCOMPATIBILITY
        else:
            pr_PraIncompatibility = self.Pr_HIGH_PRA_INCOMPATIBILITY

        if not isWifePatient:
            return pr_PraIncompatibility
        else:
            return 1.0 - self.Pr_SPOUSAL_PRA_COMPATIBILITY * (1.0 - pr_PraIncompatibility)

    def generatePair(self):
        bloodTypePatient = self.drawPatientBloodType()
        bloodTypeDonor = self.drawDonorBloodType()
        isWifePatient = self.isPatientFemale() and self.isDonorSpouse()
        patientCPRA = self.generatePraIncompatibility(isWifePatient)

        compatible = (
            bloodTypeDonor == BloodType.O and bloodTypePatient in (BloodType.A, BloodType.B, BloodType.AB, BloodType.O)
            or bloodTypeDonor == BloodType.A and bloodTypePatient in (BloodType.A, BloodType.AB)
            or bloodTypeDonor == BloodType.B and bloodTypePatient in (BloodType.B, BloodType.AB)
            or bloodTypeDonor == BloodType.AB and bloodTypePatient == BloodType.AB
        ) and not self.isPositiveCrossmatch(patientCPRA)
        
        return VertexPair(self.currentVertexID, bloodTypePatient, bloodTypeDonor, isWifePatient, patientCPRA, compatible)

    def generateAltruist(self):
        bloodTypeAltruist = self.drawDonorBloodType()
        return VertexAltruist(self.currentVertexID, bloodTypeAltruist)

    def get_blood_type_tensor(self, blood_type):
        if  blood_type==BloodType.O:
            return [1, 0, 0, 0]
        elif blood_type==BloodType.A:
            return [0, 1, 0, 0]
        elif  blood_type==BloodType.AB:
            return [0, 0, 1, 0]
        else:
            return [0, 0, 0, 1]

    def generate_synthetic(self, numPairs, numAltruists):
        pool = Pool()
        
        # Create empty lists to store the blood type arrays in 
        blood_type_donor = []
        blood_type_patient = []
        blood_type_altruists = []
        blood_cpra = []

        # generate the patient-donor pairs (PDPs)
        while self.currentVertexID < (numPairs):
            pair = self.generatePair()
            if pair.compatible is False:
                pool.addPair(pair)
                self.currentVertexID += 1
                
                # Get donor blood type tensor and append it to the list
                blood_type_tensor = self.get_blood_type_tensor(pair.bloodTypeDonor)
                blood_type_donor.append(blood_type_tensor)
                
                # Get donor patient type tensor and append it to the list
                blood_type_tensor = self.get_blood_type_tensor(pair.bloodTypePatient)
                blood_type_patient.append(blood_type_tensor)
                blood_cpra.append(pair.patientCPRA)
        
        # generate 'numAltruists'
        for _ in range(numAltruists):
            altruist = self.generateAltruist()
            pool.addAltruist(altruist)
            self.currentVertexID += 1
            
            # Get their blood type tensor and append it to the list
            blood_type_tensor = self.get_blood_type_tensor(altruist.bloodTypeDonor)
            blood_type_altruists.append(blood_type_tensor)
            blood_cpra.append(pair.patientCPRA)
  
        # Convert the blood type lists to tensors and reshape them
        blood_type_altruists = torch.tensor(blood_type_altruists)
        blood_type_donor = torch.tensor(blood_type_donor)
        blood_type_patient = torch.tensor(blood_type_patient)

        return pool, blood_type_donor, blood_type_patient, blood_type_altruists, blood_cpra

    @classmethod
    def get_pool_data_synthetic(self, num_pairs,  num_altruists):
        # Instatiate an instance of the SaidmanPoolGenerator()
        generator = SaidmanPoolGenerator()

        # Generate a Sadiman Pool
        _, blood_type_donor, blood_type_patient, blood_type_altruists, blood_cpra = generator.generate_synthetic(num_pairs, num_altruists)

        # Get the generated blood types of the donors and altruists
        blood_type_donor = torch.cat((blood_type_donor, 
                                      blood_type_altruists))
        blood_type_patient = torch.cat((blood_type_patient, 
                                        blood_type_altruists))

        # Set-up some parameter values for blood type indices and donor/patient blood type compatibility
        type_ind = dict({'O' : 0, 'A': 1, 'AB': 2, 'B': 3})
        donor_pairings = ['A/A_AB', 'B/AB_B', 'AB/AB', 'O/O_A_AB_B']

        # Create an empty matrix to store the blood type comaptiblity
        blood_edges = torch.zeros(size=(num_pairs + num_altruists, num_pairs + num_altruists))

        # for each compatible donor/recipient blood type pairing
        for pairing in donor_pairings:
            # get the indices
            split_pairing = pairing.split('/')
            donor_ind = type_ind[split_pairing[0]]
            patient_ind = [type_ind[key] for key in split_pairing[-1].split('_')]
            
            # find where the indices exist in the blood_type dataframes
            donor_index = np.where((blood_type_donor[:, donor_ind]==1))
            patient_index = np.where((blood_type_patient[:, patient_ind]==1))
            
            # expand the indices to the a size which is a function of the pool size
            type_donor_tensor = torch.tensor(donor_index[0]).view(1, -1).expand(len(patient_index[0]), -1)
            type_patient_tensor = torch.tensor(patient_index[0]).view(-1, 1).expand(-1, len(donor_index[0]))

            # place edges in the blood_edges compatiblity matrix where donor and patient are compatible
            blood_edges[type_patient_tensor, type_donor_tensor] = 1
        
        # Create a matrix of the patient cPRA values
        patient_cpra_tensor = torch.tensor(blood_cpra).view(-1, 1).expand(-1, num_pairs+num_altruists)

        # Compare the cPRA value to a matrix of random uniform values converting the boolean to a float
        # (This determines whether the edge is not present as the result of a positive crossmatch)
        type_edges = torch.rand(blood_edges.size())
        positive_crossmatch = (type_edges > patient_cpra_tensor).float()

        # Create a matrix of ones with zeros across the diagonal to remove self-loops
        cancel_self_loops = torch.ones(num_pairs + num_altruists) - torch.eye(num_pairs + num_altruists)
        
        # Generate the final edge matrix as a function of the blood type compatibility and positive crossmatches with compatibility within the pairs removed
        edges = blood_edges * positive_crossmatch * cancel_self_loops
       
        # Get the edge weighting matrix
        edge_weighting = edges.detach().clone() 

        # if there are more than zero altruists
        if num_altruists > 0:
            # Remove the value for sending a kidney from PDP/NDD to a NDD
            edge_weighting[-num_altruists:, :]=0
            
            # Remove edges between altruists
            edges[-num_altruists:, -num_altruists:]=0

            # Add a dummy edge going from all PDPs to all the NDDs
            edges[-num_altruists:, :-num_altruists]=1

        return edges, edge_weighting, blood_type_donor, blood_type_patient, blood_cpra

        # TODO: Add a method similar to addVerticesToPool found in Dickerson