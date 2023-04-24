from pudu.assembly import Protocol_from_sbol
from opentrons import protocol_api
import sbol3
# extra imports
from pydna.dseqrecord import Dseqrecord
import sbol3
from typing import List, Tuple, Union
from sbol_utilities import component
from sbol_utilities.component import dna_component_with_sequence
from sbol_utilities.helper_functions import is_plasmid
import tyto
from Bio import Restriction
#from sbol_utilities.helper_functions import find_top_level
import networkx as nx
import itertools
from sbol_utilities.conversion import convert_from_genbank
from sbol_utilities.helper_functions import find_top_level

# SBOL
def is_circular(obj: Union[sbol3.Component, sbol3.LocalSubComponent, sbol3.ExternallyDefined]) -> bool:
    """Check if an SBOL Component or Feature is circular.
    :param obj: design to be checked
    :return: true if circular
    """    
    return any(n==sbol3.SO_CIRCULAR for n in obj.types)

def is_linear(obj: Union[sbol3.Component, sbol3.LocalSubComponent, sbol3.ExternallyDefined]) -> bool:
    """Check if an SBOL Component or Feature is linear.
    :param obj: design to be checked
    :return: true if linear
    """    
    return any(n==sbol3.SO_LINEAR for n in obj.types)   

def ed_restriction_enzyme(name:str, **kwargs) -> sbol3.ExternallyDefined:
    """Creates an ExternallyDefined Restriction Enzyme Component from rebase.

    :param name: Name of the SBOL ExternallyDefined, used by PyDNA. Case sensitive, follow standard restriction enzyme nomenclature, i.e. 'BsaI'
    :param kwargs: Keyword arguments of any other ExternallyDefined attribute.
    :return: An ExternallyDefined object.
    """
    check_enzyme = Restriction.__dict__[name]
    definition=f'http://rebase.neb.com/rebase/enz/{name}.html' # TODO: replace with getting the URI from Enzyme when REBASE identifiers become available in biopython 1.8
    return sbol3.ExternallyDefined([sbol3.SBO_PROTEIN], definition=definition, name=name, **kwargs)

def backbone(identity: str, sequence: str, dropout_location: List[int], fusion_site_length:int, linear:bool, **kwargs) -> Tuple[sbol3.Component, sbol3.Sequence]:
    """Creates a Backbone Component and its Sequence.

    :param identity: The identity of the Component. The identity of Sequence is also identity with the suffix '_seq'.
    :param sequence: The DNA sequence of the Component encoded in IUPAC.
    :param dropout_location: List of 2 integers that indicates the start and the end of the dropout sequence including overhangs. Note that the index of the first location is 1, as is typical practice in biology, rather than 0, as is typical practice in computer science.
    :param fusion_site_length: Integer of the lenght of the fusion sites (eg. BsaI fusion site lenght is 4, SapI fusion site lenght is 3)
    :param linear: Boolean than indicates if the backbone is linear, by default it is seted to Flase which means that it has a circular topology.
    :param kwargs: Keyword arguments of any other Component attribute.
    :return: A tuple of Component and Sequence.
    """
    if len(dropout_location) != 2:
        raise ValueError('The dropout_location only accepts 2 int values in a list.')
    backbone_component, backbone_seq = dna_component_with_sequence(identity, sequence, **kwargs)
    backbone_component.roles.append(sbol3.SO_DOUBLE_STRANDED)  
    dropout_location_comp = sbol3.Range(sequence=backbone_seq, start=dropout_location[0], end=dropout_location[1])
    insertion_site_location1 = sbol3.Range(sequence=backbone_seq, start=dropout_location[0], end=dropout_location[0]+fusion_site_length, order=1)
    insertion_site_location2 = sbol3.Range(sequence=backbone_seq, start=dropout_location[1]-fusion_site_length, end=dropout_location[1], order=3)
    dropout_sequence_feature = sbol3.SequenceFeature(locations=[dropout_location_comp], roles=[tyto.SO.deletion])
    insertion_sites_feature = sbol3.SequenceFeature(locations=[insertion_site_location1, insertion_site_location2], roles=[tyto.SO.insertion_site])
    if linear:
        backbone_component.types.append(sbol3.SO_LINEAR)
        backbone_component.roles.append(sbol3.SO_ENGINEERED_REGION)
        open_backbone_location1 = sbol3.Range(sequence=backbone_seq, start=1, end=dropout_location[0]+fusion_site_length-1, order=1)
        open_backbone_location2 = sbol3.Range(sequence=backbone_seq, start=dropout_location[1]-fusion_site_length, end=len(sequence), order=3)
        open_backbone_feature = sbol3.SequenceFeature(locations=[open_backbone_location1, open_backbone_location2])
    else: 
        backbone_component.types.append(sbol3.SO_CIRCULAR)
        backbone_component.roles.append(tyto.SO.plasmid_vector)
        open_backbone_location1 = sbol3.Range(sequence=backbone_seq, start=1, end=dropout_location[0]+fusion_site_length-1, order=2)
        open_backbone_location2 = sbol3.Range(sequence=backbone_seq, start=dropout_location[1]-fusion_site_length, end=len(sequence), order=1)
        open_backbone_feature = sbol3.SequenceFeature(locations=[open_backbone_location1, open_backbone_location2])
    backbone_component.features.append(dropout_sequence_feature)
    backbone_component.features.append(insertion_sites_feature)
    backbone_component.features.append(open_backbone_feature)
    backbone_dropout_meets = sbol3.Constraint(restriction='http://sbols.org/v3#meets', subject=dropout_sequence_feature, object=open_backbone_feature)
    backbone_component.constraints.append(backbone_dropout_meets)
    return backbone_component, backbone_seq

def part_in_backbone2(identity: str,  sequence: str, part_location: List[int], part_roles:List[str], fusion_site_length:int, linear:bool, **kwargs) -> Tuple[sbol3.Component, sbol3.Sequence]:
    """Creates a Backbone Component and its Sequence.

    :param identity: The identity of the Component. The identity of Sequence is also identity with the suffix '_seq'.
    :param sequence: The DNA sequence of the Component encoded in IUPAC.
    :param dropout_location: List of 2 integers that indicates the start and the end of the dropout sequence including overhangs. Note that the index of the first location is 1, as is typical practice in biology, rather than 0, as is typical practice in computer science.
    :param fusion_site_length: Integer of the lenght of the fusion sites (eg. BsaI fusion site lenght is 4, SapI fusion site lenght is 3)
    :param linear: Boolean than indicates if the backbone is linear, by default it is seted to Flase which means that it has a circular topology.
    :param kwargs: Keyword arguments of any other Component attribute.
    :return: A tuple of Component and Sequence.
    """
    if len(part_location) != 2:
        raise ValueError('The part_location only accepts 2 int values in a list.')
    part_in_backbone_component, part_in_backbone_seq = dna_component_with_sequence(identity, sequence, **kwargs)
    part_in_backbone_component.roles.append(sbol3.SO_DOUBLE_STRANDED)
    for part_role in part_roles:  
        part_in_backbone_component.roles.append(part_role)  
    part_location_comp = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[0], end=part_location[1])
    insertion_site_location1 = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[0], end=part_location[0]+fusion_site_length, order=1)
    insertion_site_location2 = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[1]-fusion_site_length, end=part_location[1], order=3)
    part_sequence_feature = sbol3.SequenceFeature(locations=[part_location_comp], roles=part_roles)
    part_sequence_feature.roles.append(tyto.SO.engineered_insert)
    insertion_sites_feature = sbol3.SequenceFeature(locations=[insertion_site_location1, insertion_site_location2], roles=[tyto.SO.insertion_site])
    if linear:
        part_in_backbone_component.types.append(sbol3.SO_LINEAR)
        part_in_backbone_component.roles.append(sbol3.SO_ENGINEERED_REGION)
        open_backbone_location1 = sbol3.Range(sequence=part_in_backbone_seq, start=1, end=part_location[0]+fusion_site_length-1, order=1)
        open_backbone_location2 = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[1]-fusion_site_length, end=len(sequence), order=3)
        open_backbone_feature = sbol3.SequenceFeature(locations=[open_backbone_location1, open_backbone_location2])
    else: 
        part_in_backbone_component.types.append(sbol3.SO_CIRCULAR)
        part_in_backbone_component.roles.append(tyto.SO.plasmid_vector)
        open_backbone_location1 = sbol3.Range(sequence=part_in_backbone_seq, start=1, end=part_location[0]+fusion_site_length-1, order=2)
        open_backbone_location2 = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[1]-fusion_site_length, end=len(sequence), order=1)
        open_backbone_feature = sbol3.SequenceFeature(locations=[open_backbone_location1, open_backbone_location2])
    part_in_backbone_component.features.append(part_sequence_feature)
    part_in_backbone_component.features.append(insertion_sites_feature)
    part_in_backbone_component.features.append(open_backbone_feature)
    backbone_dropout_meets = sbol3.Constraint(restriction='http://sbols.org/v3#meets', subject=part_sequence_feature, object=open_backbone_feature)
    part_in_backbone_component.constraints.append(backbone_dropout_meets)
    return part_in_backbone_component, part_in_backbone_seq

def part_in_backbone(identity: str, part: sbol3.Component, backbone: sbol3.Component, linear:bool=False, **kwargs) -> Tuple[sbol3.Component, sbol3.Sequence]:
    """Creates a Part in Backbone Component and its Sequence.

    :param identity: The identity of the Component. The identity of Sequence is also identity with the suffix '_seq'.
    :param part: Part to be located in the backbone as SBOL Component.
    :param backbone: Backbone in wich the part is located as SBOL Component.
    :param linear: Boolean than indicates if the backbone is linear, by default it is seted to Flase which means that it has a circular topology.
    :param kwargs: Keyword arguments of any other Component attribute.
    :return: A tuple of Component and Sequence.
    """
    # check that backbone has a plasmid vector or child ontology term
    if is_plasmid(backbone)==False:
        raise TypeError('The backbone has no valid plasmid vector or child role')
    # check that the backbone and part has one sequence
    if len(backbone.sequences)!=1:
        raise ValueError(f'The backbone should have only one sequence, found {len(backbone.sequences)} sequences')
    if len(part.sequences)!=1:
        raise ValueError(f'The part should have only one sequence, found{len(part.sequences)} sequences')
    # check that the the last feature of backbone has 2 locations
    if len(backbone.features[-1].locations)!=2:
        raise ValueError(f'The backbone last feature should be the open backbone and should contain 2 Locations, found {len(backbone.features[-1].locations)} Locations')
    # get backbone sequence
    backbone_sequence = backbone.sequences[0].lookup().elements
    # compute open backbone sequences
    open_backbone_sequence_from_location1=backbone_sequence[backbone.features[-1].locations[0].start -1 : backbone.features[-1].locations[0].end]
    open_backbone_sequence_from_location2=backbone_sequence[backbone.features[-1].locations[1].start -1 : backbone.features[-1].locations[1].end]
    # extract part sequence
    part_sequence = part.sequences[0].lookup().elements
    # make new component sequence
    if linear:
        part_in_backbone_seq_str = open_backbone_sequence_from_location1 + part_sequence + open_backbone_sequence_from_location2
        topology_type = sbol3.SO_LINEAR
    else:
        part_in_backbone_seq_str = part_sequence + open_backbone_sequence_from_location2 + open_backbone_sequence_from_location1
        topology_type = sbol3.SO_CIRCULAR
    # part in backbone Component
    part_in_backbone_component, part_in_backbone_seq = dna_component_with_sequence(identity, part_in_backbone_seq_str, **kwargs)
    part_in_backbone_component.roles.append(tyto.SO.plasmid_vector) #review
    # defining Location
    part_subcomponent_location = sbol3.Range(sequence=part_in_backbone_seq, start=1, end=len(part_sequence))
    backbone_subcomponent_location = sbol3.Range(sequence=part_in_backbone_seq, start=len(part_sequence)+1, end=len(part_in_backbone_seq_str))
    source_location = sbol3.Range(sequence=backbone_sequence, start=backbone.features[-1].locations[0].start, end=backbone.features[-1].locations[0].end) # review
    # creating and adding features
    part_subcomponent = sbol3.SubComponent(part, roles=[tyto.SO.engineered_insert], locations=[part_subcomponent_location], role_integration='http://sbols.org/v3#mergeRoles')
    backbone_subcomponent = sbol3.SubComponent(backbone, locations=[backbone_subcomponent_location], source_locations=[source_location])  #[backbone.features[2].locations[0]]) #generalize source location
    part_in_backbone_component.features.append(part_subcomponent)
    part_in_backbone_component.features.append(backbone_subcomponent)
    # adding topology
    part_in_backbone_component.types.append(topology_type)
    return part_in_backbone_component, part_in_backbone_seq

def digestion(reactant:sbol3.Component, restriction_enzymes:List[sbol3.ExternallyDefined], assembly_plan:sbol3.Component, **kwargs)-> Tuple[sbol3.Component, sbol3.Sequence]:
    """Digests a Component using the provided restriction enzymes and creates a product Component and a digestion Interaction.
    The product Component is assumed to be the insert for parts in backbone and the backbone for backbones.

    :param reactant: DNA to be digested as SBOL Component. 
    :param restriction_enzymes: Restriction enzymes used  Externally Defined.
    :return: A tuple of Component and Interaction.
    """
    if sbol3.SBO_DNA not in reactant.types:
        raise TypeError(f'The reactant should has a DNA type. Types founded {reactant.types}.')
    if len(reactant.sequences)!=1:
        raise ValueError(f'The reactant needs to have precisely one sequence. The input reactant has {len(reactant.sequences)} sequences')
    participations=[]
    restriction_enzymes_pydna=[] 
    for re in restriction_enzymes:
        enzyme = Restriction.__dict__[re.name]
        restriction_enzymes_pydna.append(enzyme)
        #assembly_plan.features.append(re)
        modifier_participation = sbol3.Participation(roles=[sbol3.SBO_MODIFIER], participant=re)
        participations.append(modifier_participation)

    # Inform topology to PyDNA, if not found assuming linear. 
    if is_circular(reactant):
        circular=True
        linear=False
    else: 
        circular=False
        linear=True
        
    reactant_seq = reactant.sequences[0].lookup().elements
    # Dseqrecord is from PyDNA package with reactant sequence
    ds_reactant = Dseqrecord(reactant_seq, linear=linear, circular=circular)
    digested_reactant = ds_reactant.cut(restriction_enzymes_pydna)

    if len(digested_reactant)<2 or len(digested_reactant)>3:
        raise NotImplementedError(f'Not supported number of products. Found{len(digested_reactant)}')
    #TODO select them based on content rather than size.
    elif circular and len(digested_reactant)==2:
        part_extract, backbone = sorted(digested_reactant, key=len)
    elif linear and len(digested_reactant)==3:
        prefix, part_extract, suffix = digested_reactant
    else: raise NotImplementedError('The reactant has no valid topology type')
    
    # Extracting roles from features
    reactant_features_roles = []
    for f in reactant.features:
        for r in f.roles:
             reactant_features_roles.append(r)
    # if part
    if any(n==tyto.SO.engineered_insert for n in reactant_features_roles):
        # Compute the length of single strand sticky ends or fusion sites
        product_5_prime_ss_strand, product_5_prime_ss_end = part_extract.seq.five_prime_end()
        product_3_prime_ss_strand, product_3_prime_ss_end = part_extract.seq.three_prime_end()
    
        product_sequence = str(part_extract.seq)
        prod_comp, prod_seq = dna_component_with_sequence(identity=f'{reactant.name}_part_extract', sequence=product_sequence, **kwargs) #str(product_sequence))
        # add sticky ends features
        five_prime_fusion_site_location = sbol3.Range(sequence=product_sequence, start=1, end=len(product_5_prime_ss_end), order=1)
        three_prime_fusion_site_location = sbol3.Range(sequence=product_sequence, start=len(product_sequence)-len(product_3_prime_ss_end), end=len(product_sequence), order=3)
        fusion_sites_feature = sbol3.SequenceFeature(locations=[five_prime_fusion_site_location, three_prime_fusion_site_location], roles=[tyto.SO.insertion_site])
        prod_comp.features.append(fusion_sites_feature)

    # if backbone
    elif any(n==tyto.SO.deletion for n in reactant_features_roles):
        # Compute the length of single strand sticky ends or fusion sites
        product_5_prime_ss_strand, product_5_prime_ss_end = backbone.seq.five_prime_end()
        product_3_prime_ss_strand, product_3_prime_ss_end = backbone.seq.three_prime_end()
        product_sequence = str(backbone.seq)
        prod_comp, prod_seq = dna_component_with_sequence(identity=f'{reactant.name}_backbone', sequence=product_sequence, **kwargs) #str(product_sequence))
        # add sticky ends features
        five_prime_fusion_site_location = sbol3.Range(sequence=product_sequence, start=1, end=len(product_5_prime_ss_end), order=1)
        three_prime_fusion_site_location = sbol3.Range(sequence=product_sequence, start=len(product_sequence)-len(product_3_prime_ss_end), end=len(product_sequence), order=3)
        fusion_sites_feature = sbol3.SequenceFeature(locations=[five_prime_fusion_site_location, three_prime_fusion_site_location], roles=[tyto.SO.insertion_site])
        prod_comp.features.append(fusion_sites_feature)

    else: raise NotImplementedError('The reactant has no valid roles')

    #Add reference to part in backbone
    reactant_subcomponent = sbol3.SubComponent(reactant)
    prod_comp.features.append(reactant_subcomponent)
    # Create reactant Participation.
    react_subcomp = sbol3.SubComponent(reactant)
    assembly_plan.features.append(react_subcomp)
    reactant_participation = sbol3.Participation(roles=[sbol3.SBO_REACTANT], participant=react_subcomp)
    participations.append(reactant_participation)
    
    prod_subcomp = sbol3.SubComponent(prod_comp)
    assembly_plan.features.append(prod_subcomp)
    product_participation = sbol3.Participation(roles=[sbol3.SBO_PRODUCT], participant=prod_subcomp)
    participations.append(product_participation)
   
    # Make Interaction
    interaction = sbol3.Interaction(types=[tyto.SBO.cleavage], participations=participations)
    assembly_plan.interactions.append(interaction)
                    
    return prod_comp, prod_seq

def ligation(reactants:List[sbol3.Component], assembly_plan:sbol3.Component)-> List[Tuple[sbol3.Component, sbol3.Sequence]]:
    """Ligates Components using base complementarity and creates a product Component and a ligation Interaction.

    :param reactant: DNA to be ligated as SBOL Component. 
    :return: A tuple of Component and Interaction.
    """
    # get all fusion sites
    five_prime_fusion_sites = set()
    three_prime_fusion_sites = set()
    for r in reactants:
        five_prime_fusion_sites.add(r.sequences[0].lookup().elements[:r.features[0].locations[0].end])
        three_prime_fusion_sites.add(r.sequences[0].lookup().elements[r.features[0].locations[1].start:])

    alignments = [[r] for r in reactants] # like [[A],[B1],[B2],[C]]] and [[A,B1,C],[B1],[B2],[C]]
    used_fusion_sites = set()
    final_products = [] # [[A,B1,C]]
    while alignments:
        closed = False
        five_prime_end = False
        three_prime_end = False
        # get the first item and remove it from the list
        working_alignment = alignments[0]
        alignments.pop(0)
        # compare to all other alignments
        for alignment in alignments:
            working_alignment_5_prime_fusion_site = working_alignment[0].sequences[0].lookup().elements[:working_alignment[0].features[0].locations[0].end]
            working_alignment_3_prime_fusion_site = working_alignment[-1].sequences[0].lookup().elements[working_alignment[-1].features[0].locations[1].start:]
            alignment_5_prime_fusion_site = alignment[0].sequences[0].lookup().elements[:alignment[0].features[0].locations[0].end]
            alignment_3_prime_fusion_site = alignment[-1].sequences[0].lookup().elements[alignment[-1].features[0].locations[1].start:]
            # if working alignment 5' end matches a alignment 3' end
            if  working_alignment_5_prime_fusion_site == alignment_3_prime_fusion_site:
                # if in used_fusion_sites, skip
                if working_alignment_5_prime_fusion_site in used_fusion_sites:
                    raise ValueError(f"Fusion site {working_alignment[0].sequences[0].lookup().elements[:fusion_site_length-1]} already used")                
                else: used_fusion_sites.add(working_alignment_5_prime_fusion_site)
                # if repeated elements pass
                #if(all(x in working_alignment for x in alignment)):
                #    raise ValueError(f"Repeated elements in alignment {alignment}")

                working_alignment = alignment + working_alignment

            working_alignment_5_prime_fusion_site = working_alignment[0].sequences[0].lookup().elements[:working_alignment[0].features[0].locations[0].end]
            working_alignment_3_prime_fusion_site = working_alignment[-1].sequences[0].lookup().elements[working_alignment[-1].features[0].locations[1].start:]
            
            # if working alignment 5' end does not matches any 3' fusion site    
            if working_alignment_5_prime_fusion_site not in three_prime_fusion_sites:
                five_prime_end = True
            
            # if working_alignment is closed, add to final_products
            if working_alignment_5_prime_fusion_site == working_alignment_3_prime_fusion_site:
                final_products.append(working_alignment)
                closed = True
                break
            
            ################################################
            # if working alignment 3' end matches a alignment 5' end
            if working_alignment_3_prime_fusion_site == alignment_5_prime_fusion_site: 
                # if in used_fusion_sites, raise error
                if working_alignment_3_prime_fusion_site in used_fusion_sites:
                    raise ValueError(f"Fusion site {working_alignment[0].sequences[0].lookup().elements[:fusion_site_length-1]} already used")                
                # if repeated elements, raise error
                #if(all(x in working_alignment for x in alignment)):
                #    raise ValueError(f"Repeated elements in alignment {alignment}")
    
                working_alignment = working_alignment + alignment

            working_alignment_5_prime_fusion_site = working_alignment[0].sequences[0].lookup().elements[:working_alignment[0].features[0].locations[0].end]
            working_alignment_3_prime_fusion_site = working_alignment[-1].sequences[0].lookup().elements[working_alignment[-1].features[0].locations[1].start:]
            
            # if working alignment 5' end does not matches any 3' fusion site    
            if working_alignment_3_prime_fusion_site not in five_prime_fusion_sites:
                three_prime_end = True
            
            # if working_alignment is closed, add to final_products
            if working_alignment_5_prime_fusion_site == working_alignment_3_prime_fusion_site:
                final_products.append(working_alignment)
                closed = True
                break      
            # if no match, add to final products
            if five_prime_end and three_prime_end:
                final_products.append(working_alignment)
                break
            
            # TODO: feed working alignment to alignments
            #alignments.insert(0, working_alignment)

            # use final products to build assembly product somponent
        fusion_site_length = 4
        products_list = []
        participations = []
        for composite in final_products: # a composite of the form [A,B,C]
            composite_number = 0
            # calculate sequence
            composite_sequence_str = ""
            composite_name = ""
            #part_subcomponents = []
            part_extract_subcomponents = []
            for part_extract in composite:
                composite_sequence_str = composite_sequence_str + part_extract.sequences[0].lookup().elements[:-fusion_site_length] #needs a version for linear
                # create participations
                part_extract_subcomponent = sbol3.SubComponent(part_extract) # LocalSubComponent??
                part_extract_subcomponents.append(part_extract_subcomponent)
                # if not in assembl plan?
                #assembly_plan.features.append(part_extract_subcomponent) # should be saved at composite level
                #part_subcomponents.append(part_subcomponent)
                #part_participation = sbol3.Participation(roles=[sbol3.SBO_REACTANT], participant=part_subcomponent)
                #participations.append(part_participation)
                composite_name = composite_name + part_extract.name
            # create dna componente and sequence
            composite_component, composite_seq = dna_component_with_sequence(f'composite_{composite_number}_{composite_name}', composite_sequence_str) # **kwarads use in future?
            composite_component.roles.append(sbol3.SO_ENGINEERED_REGION)
            composite_component.features = part_extract_subcomponents
            # TODO fix order of features
            #composite_component.constraints.append(sbol3.Constraint(sbol3.SBOL_MEETS, composite_component.features[composite_number-1], composite_component.features[composite_number]))
            # add product participation 
            #composite_subcomponent = sbol3.SubComponent(composite_component)
            #participations.append(sbol3.Participation(roles=[sbol3.SBO_PRODUCT], participant=composite_subcomponent))
            # create interactions
            #assembly_plan.interactions.append(sbol3.Interaction(types=[tyto.SBO.conversion], participations=participations))
            products_list.append([composite_component, composite_seq])
            composite_number += 1
    #create preceed constrain
    #create composite part or part in backbone
    #add interactions to assembly_plan
    #add participations to assembly_plan

    return products_list

class Assembly_plan_composite_in_backbone_single_enzyme():
    """Creates a Assembly Plan.
    #classes uses param here?
    :param parts_in_backbone: Parts in backbone to be assembled. 
    :param acceptor_backbone:  Backbone in which parts are inserted on the assembly. 
    :param restriction_enzymes: Restriction enzyme with correct name from Bio.Restriction as Externally Defined.
    :param linear: Boolean to inform if the reactant is linear.
    :param circular: Boolean to inform if the reactant is circular.
    :param **kwargs: Keyword arguments of any other Component attribute for the assembled part.
    """

    def __init__(self, name: str, parts_in_backbone: List[sbol3.Component], acceptor_backbone: sbol3.Component, restriction_enzyme: Union[str,sbol3.ExternallyDefined], document:sbol3.Document):
        self.name = name
        self.parts_in_backbone = parts_in_backbone
        self.acceptor_backbone = acceptor_backbone
        self.restriction_enzyme = restriction_enzyme
        self.products = []
        self.extracted_parts = []
        self.document = document

        #create assembly plan
        self.assembly_plan_component = sbol3.Component(identity=f'{self.name}_assembly_plan', types=sbol3.SBO_FUNCTIONAL_ENTITY)
        self.document.add(self.assembly_plan_component)
        self.composites = []

    def run(self):
        self.assembly_plan_component.features.append(self.restriction_enzyme)
        #store reactant c
        #extract parts
        part_number = 1
        for part_in_backbone in self.parts_in_backbone:
            part_comp, part_seq = digestion(reactant=part_in_backbone,restriction_enzymes=[self.restriction_enzyme], assembly_plan=self.assembly_plan_component, name=f'part_{part_number}')
            self.document.add([part_comp, part_seq])
            self.extracted_parts.append(part_comp)
            part_number += 1

        #extract backbone (should be the same?)
        backbone_comp, backbone_seq = digestion(reactant=self.acceptor_backbone,restriction_enzymes=[self.restriction_enzyme], assembly_plan=self.assembly_plan_component,  name=f'part_{part_number}')
        self.document.add([backbone_comp, backbone_seq])
        self.extracted_parts.append(backbone_comp)
        
        #create composite part from extracted parts
        composites_list = ligation(reactants=self.extracted_parts, assembly_plan=self.assembly_plan_component)
        for composite in composites_list:
            composite[0].generated_by.append(self.assembly_plan_component) #
            self.composites.append(composite)
            self.products.append(composite)
            self.document.add(composite)


        #generate all the relationships in SEP055

def part_in_backbone_from_sbol(identity: str,  sbol3_comp: sbol3.Component, part_location: List[int], part_roles:List[str], fusion_site_length:int, linear:bool=False, **kwargs) -> Tuple[sbol3.Component, sbol3.Sequence]:
    """Creates a Part in Backbone Component and its Sequence following BP011 from an unformatted SBOL3 Component.
    It overwrites the SBOL3 Component provided. 
    A part inserted into a backbone is represented by a Component that includes both the part insert 
    as a feature that is a SubComponent and the backbone as another SubComponent.
    For more information about BP011 visit https://github.com/SynBioDex/SBOL-examples/tree/main/SBOL/best-practices/BP011 

    :param identity: The identity of the Component. The identity of Sequence is also identity with the suffix '_seq'.
    :param sbol3_comp: The SBOL3 Component that will be used to create the part in backbone Component and Sequence.
    :param part_location: List of 2 integers that indicates the start and the end of the unitary part. Note that the index of the first location is 1, as is typical practice in biology, rather than 0, as is typical practice in computer science.
    :param part_roles: List of strings that indicates the roles of the part.
    :param fusion_site_length: Integer of the length of the fusion sites (eg. BsaI fusion site lenght is 4, SapI fusion site lenght is 3)
    :param linear: Boolean than indicates if the backbone is linear, by default it is seted to Flase which means that it has a circular topology.    
    :param kwargs: Keyword arguments of any other Component attribute.
    :return: A tuple of Component and Sequence.
    """
    if len(part_location) != 2:
        raise ValueError('The part_location only accepts 2 int values in a list.')
    if len(sbol3_comp.sequences)!=1:
        raise ValueError(f'The reactant needs to have precisely one sequence. The input reactant has {len(sbol3_comp.sequences)} sequences')
    sequence = sbol3_comp.sequences[0].lookup().elements
    part_in_backbone_component, part_in_backbone_seq = dna_component_with_sequence(identity, sequence, **kwargs)
    part_in_backbone_component.roles.append(sbol3.SO_DOUBLE_STRANDED)
    for part_role in part_roles:  
        part_in_backbone_component.roles.append(part_role)  
    # creating part feature    
    part_location_comp = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[0], end=part_location[1])
    #TODO: add the option of fusion sites to be of different lenghts
    insertion_site_location1 = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[0], end=part_location[0]+fusion_site_length, order=1)
    insertion_site_location2 = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[1]-fusion_site_length, end=part_location[1], order=3)
    part_sequence_feature = sbol3.SequenceFeature(locations=[part_location_comp], roles=part_roles)
    part_sequence_feature.roles.append(tyto.SO.engineered_insert)
    insertion_sites_feature = sbol3.SequenceFeature(locations=[insertion_site_location1, insertion_site_location2], roles=[tyto.SO.insertion_site])
    if linear:
        part_in_backbone_component.types.append(sbol3.SO_LINEAR)
        part_in_backbone_component.roles.append(sbol3.SO_ENGINEERED_REGION)
        # creating backbone feature
        open_backbone_location1 = sbol3.Range(sequence=part_in_backbone_seq, start=1, end=part_location[0]+fusion_site_length-1, order=1)
        open_backbone_location2 = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[1]-fusion_site_length, end=len(sequence), order=3)
        open_backbone_feature = sbol3.SequenceFeature(locations=[open_backbone_location1, open_backbone_location2])
    else: 
        part_in_backbone_component.types.append(sbol3.SO_CIRCULAR)
        part_in_backbone_component.roles.append(tyto.SO.plasmid_vector)
        # creating backbone feature
        open_backbone_location1 = sbol3.Range(sequence=part_in_backbone_seq, start=1, end=part_location[0]+fusion_site_length-1, order=2)
        open_backbone_location2 = sbol3.Range(sequence=part_in_backbone_seq, start=part_location[1]-fusion_site_length, end=len(sequence), order=1)
        open_backbone_feature = sbol3.SequenceFeature(locations=[open_backbone_location1, open_backbone_location2])
    part_in_backbone_component.features.append(part_sequence_feature)
    part_in_backbone_component.features.append(insertion_sites_feature)
    part_in_backbone_component.features.append(open_backbone_feature)
    backbone_dropout_meets = sbol3.Constraint(restriction='http://sbols.org/v3#meets', subject=part_sequence_feature, object=open_backbone_feature)
    part_in_backbone_component.constraints.append(backbone_dropout_meets)
    #TODO: Add a branch to create a component without overwriting the WHOLE input component
    return part_in_backbone_component, part_in_backbone_seq

# Docsument start
doc = sbol3.Document()
sbol3.set_namespace('https://github.com/Gonza10V')
bsai = ed_restriction_enzyme('BsaI')
lvl1_pOdd_acceptor_seq = 'gctcgagtcccgtcaagtcagcgtaatgctctgccagtgttacaaccaattaaccaattctgattagaaaaactcatcgagcatcaaatgaaactgcaatttattcatatcaggattatcaataccatatttttgaaaaagccgtttctgtaatgaaggagaaaactcaccgaggcagttccataggatggcaagatcctggtatcggtctgcgattccgactcgtccaacatcaatacaacctattaatttcccctcgtcaaaaataaggttatcaagtgagaaatcaccatgagtgacgactgaatccggtgagaatggcaaaagcttatgcatttctttccagacttgttcaacaggccagccattacgctcgtcatcaaaatcactcgcatcaaccaaaccgttattcattcgtgattgcgcctgagcgagacgaaatacgcgatcgctgttaaaaggacaattacaaacaggaatcgaatgcaaccggcgcaggaacactgccagcgcatcaacaatattttcacctgaatcaggatattcttctaatacctggaatgctgttttcccggggatcgcagtggtgagtaaccatgcatcatcaggagtacggataaaatgcttgatggtcggaagaggcataaattccgtcagccagtttagtctgaccatctcatctgtaacatcattggcaacgctacctttgccatgtttcagaaacaactctggcgcatcgggcttcccatacaatcgatagattgtcgcacctgattgcccgacattatcgcgagcccatttatacccatataaatcagcatccatgttggaatttaatcgcggcctggagcaagacgtttcccgttgaatatggctcataacaccccttgtattactgtttatgtaagcagacagttttattgttcatgatgatatatttttatcttgtgcaatgtaacatcagagattttgagacacaacgtggctttgttgaataaatcgaacttttgctgagttgaaggatcagctcgagtgccacctgacgtctaagaaaccattattatcatgacattaacctataaaaataggcgtatcacgaggcagaatttcagataaaaaaaatccttagctttcgctaaggatgatttctggaattcgctcttcaatgggagtgagacccaatacgcaaaccgcctctccccgcgcgttggccgattcattaatgcagctggcacgacaggtttcccgactggaaagcgggcagtgagcgcaacgcaattaatgtgagttagctcactcattaggcaccccaggctttacactttatgcttccggctcgtatgttgtgtggaattgtgagcggataacaatttcacacatactagagaaagaggagaaatactagatggcttcctccgaagacgttatcaaagagttcatgcgtttcaaagttcgtatggaaggttccgttaacggtcacgagttcgaaatcgaaggtgaaggtgaaggtcgtccgtacgaaggtacccagaccgctaaactgaaagttaccaaaggtggtccgctgccgttcgcttgggacatcctgtccccgcagttccagtacggttccaaagcttacgttaaacacccggctgacatcccggactacctgaaactgtccttcccggaaggtttcaaatgggaacgtgttatgaacttcgaagacggtggtgttgttaccgttacccaggactcctccctgcaagacggtgagttcatctacaaagttaaactgcgtggtaccaacttcccgtccgacggtccggttatgcagaaaaaaaccatgggttgggaagcttccaccgaacgtatgtacccggaagacggtgctctgaaaggtgaaatcaaaatgcgtctgaaactgaaagacggtggtcactacgacgctgaagttaaaaccacctacatggctaaaaaaccggttcagctgccgggtgcttacaaaaccgacatcaaactggacatcacctcccacaacgaagactacaccatcgttgaacagtacgaacgtgctgaaggtcgtcactccaccggtgcttaataacgctgatagtgctagtgtagatcgctactagagccaggcatcaaataaaacgaaaggctcagtcgaaagactgggcctttcgttttatctgttgtttgtcggtgaacgctctctactagagtcacactggctcaccttcgggtgggcctttctgcgtttataggtctcaCGCTgcatgaagagcctgcagtccggcaaaaaagggcaaggtgtcaccaccctgccctttttctttaaaaccgaaaagattacttcgcgttatgcaggcttcctcgctcactgactcgctgcgctcggtcgttcggctgcggcgagcggtatcagctcactcaaaggcggtaatacggttatccacagaatcaggggataacgcaggaaagaacatgtgagcaaaaggccagcaaaaggccaggaaccgtaaaaaggccgcgttgctggcgtttttccacaggctccgcccccctgacgagcatcacaaaaatcgacgctcaagtcagaggtggcgaaacccgacaggactataaagataccaggcgtttccccctggaagctccctcgtgcgctctcctgttccgaccctgccgcttaccggatacctgtccgcctttctcccttcgggaagcgtggcgctttctcatagctcacgctgtaggtatctcagttcggtgtaggtcgttcgctccaagctgggctgtgtgcacgaaccccccgttcagcccgaccgctgcgccttatccggtaactatcgtcttgagtccaacccggtaagacacgacttatcgccactggcagcagccactggtaacaggattagcagagcgaggtatgtaggcggtgctacagagttcttgaagtggtggcctaactacggctacactagaagaacagtatttggtatctgcgctctgctgaagccagttaccttcggaaaaagagttggtagctcttgatccggcaaacaaaccaccgctggtagcggtggtttttttgtttgcaagcagcagattacgcgcagaaaaaaaggatctcaagaagatcctttgatcttttctacggggtctgacgctcagtggaacgaaaactcacgttaagggattttggtcatgagattatcaaaaaggatcttcacctagatccttttaaattaaaaatgaagttttaaatcaatctaaagtatatatgagtaaacttggtctgaca'
podd_backbone, podd_backbone_seq = backbone('pOdd_bb', lvl1_pOdd_acceptor_seq, [1169,2259], 4, False, name='pOdd_bb')
doc.add([podd_backbone,podd_backbone_seq])
j23100_b0034_doc = convert_from_genbank('./scripts/files/j23100_b0034.gb', 'https://github.com/Gonza10V')
j23100_b0034_ac = [top_level for top_level in j23100_b0034_doc if type(top_level)==sbol3.Component][0]
sfgfp_doc = convert_from_genbank('./scripts/files/sfgfp.gb', 'https://github.com/Gonza10V')
sfgfp_ce = [top_level for top_level in sfgfp_doc if type(top_level)==sbol3.Component][0]
b0015_doc = convert_from_genbank('./scripts/files/b0015.gb', 'https://github.com/Gonza10V')
b0015_ef = [top_level for top_level in b0015_doc if type(top_level)==sbol3.Component][0]
j23100_b0034_ac_in_bb, j23100_b0034_ac_in_bb_seq = part_in_backbone_from_sbol('j23100_b0034_ac_in_bb', j23100_b0034_ac, [476,545], [sbol3.SO_PROMOTER, sbol3.SO_RBS], 4, False, name='j23100_b0034_ac_in_bb')
doc.add([j23100_b0034_ac_in_bb, j23100_b0034_ac_in_bb_seq])
sfgfp_ce_in_bb, sfgfp_ce_in_bb_seq = part_in_backbone_from_sbol('sfgfp_ce_in_bb', sfgfp_ce, [130,854], [sbol3.SO_CDS], 4, False, name='sfgfp_ce_in_bb')
doc.add([sfgfp_ce_in_bb, sfgfp_ce_in_bb_seq])
b0015_ef_in_bb, b0015_ef_in_bb_seq = part_in_backbone_from_sbol('b0015_ef_in_bb', b0015_ef, [518,646], [sbol3.SO_TERMINATOR], 4, False, name='b0015_ef_in_bb')
doc.add([b0015_ef_in_bb, b0015_ef_in_bb_seq])
assembly_plan_automation = Assembly_plan_composite_in_backbone_single_enzyme( 
                            name='constitutive_gfp_tu',
                            parts_in_backbone=[j23100_b0034_ac_in_bb, sfgfp_ce_in_bb, b0015_ef_in_bb], 
                            acceptor_backbone=podd_backbone,
                            restriction_enzyme=bsai,
                            document=doc)
assembly_plan_automation.run()

#OT2 protocol
# metadata
metadata = {
'protocolName': 'PUDU SBOL assembly',
'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
'description': 'Automated DNA assembly protocol',
'apiLevel': '2.13'}



def run(protocol= protocol_api.ProtocolContext):

    pudu_protocol_from_sbol = Protocol_from_sbol(assembly_plan=assembly_plan_automation, thermocycler_starting_well=1)
    pudu_protocol_from_sbol.run(protocol)
    #chained actions
    #save sbol
    doc = sbol3.Document()
    doc.add(pudu_protocol_from_sbol.sbol_output)
    doc.write('pudu_protocol_from_sbol.nt', sbol3.SORTED_NTRIPLES)
    #save xlsx
    pudu_protocol_from_sbol.get_xlsx_output('pudu_protocol_from_sbol')


