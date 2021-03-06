""" Tests of the knowledge base core schema

:Author: Balazs Szigeti <balazs.szigeti@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Author: Bilal Shaikh <bilal.shaikh@columbia.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Yin Hoon Chew <yinhoon.chew@mssm.edu>
:Date: 2018-02-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_kb import core
from wc_onto import onto as kbOnt
from wc_utils.util import chem
from wc_utils.util.units import unit_registry
from wc_utils.util.ontology import are_terms_equivalent
import Bio.Alphabet
import Bio.Seq
import Bio.SeqIO
import Bio.SeqUtils
import mendeleev
import numpy
import os
import shutil
import tempfile
import unittest


class TestCore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        records = Bio.SeqIO.parse('tests/fixtures/prokaryote_seq.fna', 'fasta')
        cls.chr_seq = next(records).seq


# JUNK TESTS
class ReferenceTestCase(unittest.TestCase):
    def test_constructor(self):
        ref1 = core.Reference(id='ref1')
        self.assertEqual(ref1.id, 'ref1')


class KnowledgeBaseTestCase(unittest.TestCase):

    def test_get_nested_metadata(self):

        cell1 = core.Cell(id='cell1')
        kb = core.KnowledgeBase(cell = cell1)
        met = core.MetaboliteSpeciesType(id='met1', cell=cell1)

        # Test null case
        self.assertEqual(met.get_nested_metadata(),
                        {'met1': [], core.SpeciesTypeProperty: [],
                        core.Evidence: [], core.Experiment:[]})

        # Load min KB to test some relationships
        ref1=core.Reference(id='ref1')
        ref2=core.Reference(id='ref2')

        met2 = core.MetaboliteSpeciesType(id='met2', cell=cell1, references=[ref1, ref2], comments = 'test comment')
        self.assertEqual(met2.get_nested_metadata(),
            {'met2': [ref1, ref2, 'test comment'],
            core.SpeciesTypeProperty: [],
            core.Evidence: [],
            core.Experiment: []})

        ref3 = core.Reference(id='ref3')
        dbref1 = core.Identifier(id='dbref1')
        exp1 = core.Experiment(id='exp1', references = [ref3], comments = 'exp comment')
        evi1 = core.Evidence(id='evi1', experiment=exp1, comments = 'evidence comment')
        stp = core.SpeciesTypeProperty(id='stp1', evidence=[evi1], identifiers=[dbref1], references = [ref1])
        met3 = core.MetaboliteSpeciesType(id='met3', cell=cell1, properties = [stp], comments='met comment')

        self.assertEqual(met3.get_nested_metadata(),
            {'met3': ['met comment'],
             core.SpeciesTypeProperty: [ref1, dbref1],
             core.Evidence: ['evidence comment'],
             core.Experiment: [ref3, 'exp comment']})


# JUNK TESTS
class CellTestCase(unittest.TestCase):
    def test_constructor(self):
        cell = core.Cell()

        self.assertEqual(cell.knowledge_base, None)
        self.assertEqual(cell.taxon, None)
        self.assertEqual(cell.observables, [])
        self.assertEqual(cell.species_types, [])
        self.assertEqual(cell.compartments, [])
        self.assertEqual(cell.reactions, [])
        self.assertEqual(cell.loci, [])

        self.assertEqual(cell.species_types.get(
            __type=core.DnaSpeciesType), [])


# JUNK TESTS
class CompartmentTestCase(unittest.TestCase):
    def test_constructor(self):
        comp = core.Compartment(volumetric_fraction=0.5)
        self.assertEqual(comp.volumetric_fraction, 0.5)


# JUNK TESTS
class SpeciesTypeTestCase(unittest.TestCase):
    def test_constructor(self):
        with self.assertRaisesRegex(TypeError, 'Can\'t instantiate abstract class'):
            core.SpeciesType()

        class ConcreteSpeciesType(core.SpeciesType):
            def get_empirical_formula(self): pass

            def get_charge(self): pass

            def get_mol_wt(self): pass

        species_type = ConcreteSpeciesType(
            id='species1', name='species1')
        self.assertEqual(species_type.id, 'species1')
        self.assertEqual(species_type.name, 'species1')


# JUNK TESTS
class ConcentrationTestCase(unittest.TestCase):
    def test_constructor(self):
        comp = core.Compartment(id='c')
        met = core.MetaboliteSpeciesType(id='met')
        spec = core.Species(species_type=met, compartment=comp)
        conc = core.Concentration(species=spec, value=0.2)

        self.assertEqual(conc.serialize(), 'CONC[met[c]]')
        self.assertEqual(conc.value, 0.2)
        self.assertEqual(conc.units, unit_registry.parse_units('molar'))


# Organized + cover + passes
class IdentifierTestCase(unittest.TestCase):

    def test_serialize(self):
        identifier1 = core.Identifier(namespace='Sabio-Rk', id='123456')
        self.assertEqual(identifier1.serialize(), 'Sabio-Rk:123456')

        identifier2 = core.Identifier(namespace='KEGG', id='00')
        self.assertEqual(identifier2.serialize(), 'KEGG:00')


class IdentifierAttributeTestCase(unittest.TestCase):

    def test_serialize(self):
        identifier1 = core.Identifier(namespace='Sabio-Rk', id='123456')
        identifier2 = core.Identifier(namespace='KEGG', id='00')

        self.assertEqual(core.IdentifierAttribute().serialize(
            [identifier1, identifier2]), 'Sabio-Rk:123456, KEGG:00')

    def test_deserialize(self):
        identifier1 = core.Identifier(namespace='Sabio-Rk', id='123456')
        identifier2 = core.Identifier(namespace='KEGG', id='00')

        objects = {
            core.Identifier: {
                'Sabio-Rk:123456': identifier1,
                'KEGG:00': identifier2,
            }
        }

        result = core.IdentifierAttribute().deserialize(
            value='Sabio-Rk:123456, KEGG:00', objects=objects)
        self.assertEqual(result[1], None)
        self.assertEqual(result[0][0].namespace, 'Sabio-Rk')
        self.assertEqual(result[0][0].id, '123456')
        self.assertEqual(result[0][1].namespace, 'KEGG')
        self.assertEqual(result[0][1].id, '00')


# Done
class SpeciesTestCase(unittest.TestCase):

    def test_gen_id(self):
        comp1 = core.Compartment(id='c')
        met1 = core.MetaboliteSpeciesType(id='met1')
        species1 = core.Species(species_type=met1, compartment=comp1)

        self.assertEqual(species1.id(), 'met1[c]')
        self.assertEqual(core.Species.gen_id(met1, comp1), 'met1[c]')
        self.assertEqual(core.Species.gen_id('met1', 'c'), 'met1[c]')

        with self.assertRaisesRegex(ValueError, 'incorrect species type'):
            core.Species.gen_id(None, 'c')
        with self.assertRaisesRegex(ValueError, 'incorrect compartment type'):
            core.Species.gen_id('met1', None)

    def test_serialize(self):
        comp1 = core.Compartment(id='c')
        met1 = core.MetaboliteSpeciesType(id='met1')
        species1 = core.Species(species_type=met1, compartment=comp1)

        self.assertEqual(species1.serialize(), 'met1[c]')

    def test_deserialize(self):
        comp1 = core.Compartment(id='c')
        met1 = core.MetaboliteSpeciesType(id='1met1')
        dna1 = core.DnaSpeciesType(id='dna1')

        objects = {
            core.Compartment: {
                'c': comp1,
            },
            core.MetaboliteSpeciesType: {
                '1met1': met1,
            },
            core.DnaSpeciesType: {
                'dna1': dna1,
            },
        }

        attr = core.SpeciesCoefficient.species
        result = core.Species.deserialize(attr, '1met1[c]', objects)
        self.assertEqual(result[0].species_type, met1)
        self.assertEqual(result[0].compartment, comp1)
        self.assertEqual(result[1], None)

        result2 = core.Species.deserialize(attr, '1met1[c]', objects)
        self.assertEqual(result2[0], result[0])
        self.assertIn(core.Species, objects)
        self.assertIn('1met1[c]', objects[core.Species])

        self.assertNotIn('dna1[c]', objects[core.Species])
        self.assertEqual(core.Species.deserialize(
            attr, 'dna1[c]', objects)[1], None)
        self.assertIn('dna1[c]', objects[core.Species])

        self.assertNotEqual(core.Species.deserialize(
            attr, 'met2[c]', objects)[1], None)
        self.assertNotEqual(core.Species.deserialize(
            attr, '1met1[e]', objects)[1], None)
        self.assertNotEqual(core.Species.deserialize(
            attr, '1met1', objects)[1], None)


# Done
class PolymerSpeciesTypeTestCase(unittest.TestCase):

    def setUp(self):

        class ConcretePolymerSpeciesType(core.PolymerSpeciesType):
            def get_empirical_formula(self): pass
            def get_charge(self): pass
            def get_mol_wt(self): pass
            def get_seq(self): return Bio.Seq.Seq(
                'AAATGCCC', alphabet=Bio.Alphabet.DNAAlphabet())

        self.pst1 = ConcretePolymerSpeciesType(id='pst1', name='pst1')

    def tearDown(self):
        pass

    def test_get_seq(self):

        with self.assertRaisesRegex(TypeError, 'Can\'t instantiate abstract class'):
            core.PolymerSpeciesType()

        self.pst1.circular = False
        self.pst1.double_stranded = False
        self.assertEqual(self.pst1.get_seq(), 'AAATGCCC')

        self.pst1.circular = True
        self.pst1.double_stranded = False
        self.assertEqual(self.pst1.get_seq(), 'AAATGCCC')

        self.pst1.circular = True
        self.pst1.double_stranded = True
        self.assertEqual(self.pst1.get_seq(), 'AAATGCCC')

    def test_get_len(self):

        self.pst1.circular = False
        self.pst1.double_stranded = False
        self.assertEqual(self.pst1.get_len(), 8)

        self.pst1.circular = True
        self.pst1.double_stranded = False
        self.assertEqual(self.pst1.get_len(), 8)

        self.pst1.circular = True
        self.pst1.double_stranded = True
        self.assertEqual(self.pst1.get_len(), 8)

    def test_get_subseq(self):

        self.pst1.circular = False
        self.pst1.double_stranded = False
        self.assertEqual(self.pst1.get_subseq(1, 3), 'AAA')
        self.assertEqual(self.pst1.get_subseq(2, 4), 'AAT')
        with self.assertRaisesRegex(ValueError, 'Start and end coordinates'):
            self.assertEqual(self.pst1.get_subseq(-1, 3), 'AAA')

        self.pst1.circular = True
        self.pst1.double_stranded = False
        self.assertEqual(self.pst1.get_subseq(2, 4), 'AAT')
        self.assertEqual(self.pst1.get_subseq(0, 1), 'CA')
        self.assertEqual(self.pst1.get_subseq(-3, 1), 'GCCCA')
        self.assertEqual(self.pst1.get_subseq(6, 10), 'CCCAA')
        self.assertEqual(self.pst1.get_subseq(-10, 10), 'CCCAAATGCCCAAATGCCCAA')

        self.pst1.circular = True
        self.pst1.double_stranded = True
        self.assertEqual(self.pst1.get_subseq(
            3,  6, strand=core.PolymerStrand.positive), 'ATGC')
        self.assertEqual(self.pst1.get_subseq(
            3,  6, strand=core.PolymerStrand.negative), 'GCAT')
        self.assertEqual(self.pst1.get_subseq(
            6, 26, strand=core.PolymerStrand.positive), 'CCCAAATGCCCAAATGCCCAA')
        self.assertEqual(self.pst1.get_subseq(
            6, 26, strand=core.PolymerStrand.negative), 'TTGGGCATTTGGGCATTTGGG')


#Disorganized
class DnaSpeciesTypeTestCase(unittest.TestCase):
    def test(self):
        self.tmp_dirname = tempfile.mkdtemp()
        filepath = os.path.join(self.tmp_dirname, 'test_seq.fasta')
        with open(filepath, 'w') as f:
            f.write('>dna1\nACGTACGT\n'
                    '>dna2\nACGTACGTNNNN\n')

        dna = core.DnaSpeciesType(id='dna1', name='dna1', sequence_path=filepath,
                                  circular=False, double_stranded=False, ploidy=2)

        self.assertEqual(dna.id, 'dna1')
        self.assertEqual(dna.name, 'dna1')
        self.assertEqual(dna.circular, False)
        self.assertEqual(dna.double_stranded, False)
        self.assertEqual(dna.ploidy, 2)

        L = dna.get_len()
        self.assertEqual(dna.get_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O6P') * 2
                         + chem.EmpiricalFormula('C9H12N3O7P') * 2
                         + chem.EmpiricalFormula('C10H12N5O7P') * 2
                         + chem.EmpiricalFormula('C10H13N2O8P') * 2
                         - chem.EmpiricalFormula('OH') * (L - 1)
                         )

        self.assertEqual(dna.get_charge(), -L - 1)
        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(dna.get_seq(),
                                            seq_type='DNA',
                                            circular=dna.circular,
                                            double_stranded=dna.double_stranded) \
            - 9 * mendeleev.element('H').atomic_weight

        self.assertAlmostEqual(dna.get_mol_wt(), exp_mol_wt, places=0)

        # Make DNA circular, single stranded
        dna.circular = True
        dna.double_stranded = False

        self.assertEqual(dna.get_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O6P') * 2
                         + chem.EmpiricalFormula('C9H12N3O7P') * 2
                         + chem.EmpiricalFormula('C10H12N5O7P') * 2
                         + chem.EmpiricalFormula('C10H13N2O8P') * 2
                         - chem.EmpiricalFormula('OH') * L
                         )

        self.assertEqual(dna.get_charge(), -L)

        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(dna.get_seq(),
                                            seq_type='DNA',
                                            circular=dna.circular,
                                            double_stranded=dna.double_stranded) \
            - 8 * mendeleev.element('H').atomic_weight

        self.assertAlmostEqual(dna.get_mol_wt(), exp_mol_wt, places=0)

        # Make DNA linear, double stranded
        dna.circular = False
        dna.double_stranded = True

        self.assertEqual(dna.get_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O6P') * 2 * 2
                         + chem.EmpiricalFormula('C9H12N3O7P') * 2 * 2
                         + chem.EmpiricalFormula('C10H12N5O7P') * 2 * 2
                         + chem.EmpiricalFormula('C10H13N2O8P') * 2 * 2
                         - chem.EmpiricalFormula('OH') * (L - 1) * 2
                         )

        self.assertEqual(dna.get_charge(), 2 * (-L - 1))
        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(dna.get_seq(),
                                            seq_type='DNA',
                                            circular=dna.circular,
                                            double_stranded=dna.double_stranded) \
            - 18 * mendeleev.element('H').atomic_weight

        self.assertAlmostEqual(dna.get_mol_wt(), exp_mol_wt, places=0)

        # Make DNA circular, double stranded
        dna.circular = True
        dna.double_stranded = True

        self.assertEqual(dna.get_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O6P') * 2 * 2
                         + chem.EmpiricalFormula('C9H12N3O7P') * 2 * 2
                         + chem.EmpiricalFormula('C10H12N5O7P') * 2 * 2
                         + chem.EmpiricalFormula('C10H13N2O8P') * 2 * 2
                         - chem.EmpiricalFormula('OH') * L * 2
                         )

        self.assertEqual(dna.get_charge(), 2 * -L)

        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(dna.get_seq(),
                                            seq_type='DNA',
                                            circular=dna.circular,
                                            double_stranded=dna.double_stranded) \
            - 16 * mendeleev.element('H').atomic_weight

        self.assertAlmostEqual(dna.get_mol_wt(), exp_mol_wt, places=0)

        # If there are N's in the DNA sequence
        dna2 = core.DnaSpeciesType(id='dna2', sequence_path=filepath,
                                   circular=False, double_stranded=True)

        L = dna2.get_len()
        self.assertEqual(dna2.get_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O6P') * 3 * 2
                         + chem.EmpiricalFormula('C9H12N3O7P') * 3 * 2
                         + chem.EmpiricalFormula('C10H12N5O7P') * 3 * 2
                         + chem.EmpiricalFormula('C10H13N2O8P') * 3 * 2
                         - chem.EmpiricalFormula('OH') * (L - 1) * 2
                         )

        shutil.rmtree(self.tmp_dirname)


# Done
class PolymerLocusTestCase(unittest.TestCase):

    def setUp(self):

        cell1 = core.Cell()
        self.tmp_dirname = tempfile.mkdtemp()
        filepath = os.path.join(self.tmp_dirname, 'test_seq.fasta')
        with open(filepath, 'w') as f:
            f.write('>dna1\nACGTACGTACGTACG\n')

        self.dna1 = core.DnaSpeciesType(id='dna1', sequence_path=filepath,
                                   circular=False, double_stranded=False)

        self.locus1 = core.PolymerLocus(id='locus1', cell=cell1, name='locus1', polymer=self.dna1,
                                   strand=core.PolymerStrand.positive, start=1, end=15)

        self.locus2 = core.PolymerLocus(id='locus2', cell=cell1, name='locus2', polymer=self.dna1,
                                   strand=core.PolymerStrand.positive, start=14, end=2)

    def tearDown(self):
        shutil.rmtree(self.tmp_dirname)

    def test_seq(self):

        self.assertEqual(self.locus1.get_seq(), 'ACGTACGTACGTACG')

        rev_comp_seq = self.locus1.get_seq().reverse_complement()
        self.locus1.strand = core.PolymerStrand.negative
        self.assertEqual(self.locus1.get_seq(), rev_comp_seq)

    def test_len(self):

        self.assertEqual(self.locus1.get_len(), 15)
        rev_comp_seq = self.locus1.get_seq().reverse_complement()
        self.locus1.strand = core.PolymerStrand.negative
        self.assertEqual(self.locus1.get_len(), 15)

    def test_get_direction(self):

        self.assertTrue(are_terms_equivalent(self.locus1.get_direction(), core.PolymerDirection.forward))
        self.assertTrue(are_terms_equivalent(self.locus2.get_direction(), core.PolymerDirection.reverse))

        self.locus1.strand = core.PolymerStrand.negative
        self.locus2.strand = core.PolymerStrand.negative
        self.assertTrue(are_terms_equivalent(self.locus1.get_direction(), core.PolymerDirection.reverse))
        self.assertTrue(are_terms_equivalent(self.locus2.get_direction(), core.PolymerDirection.forward))

        self.locus1.start = 15
        self.locus1.end   = 15
        with self.assertRaises(ValueError):
            self.locus1.get_direction()

class MetaboliteSpeciesTypeTestCase(unittest.TestCase):
    def test_constructor(self):       
        prop1 = core.SpeciesTypeProperty(
            property = 'empirical_formula',
            value_type = kbOnt['WC:string'],
            value = 'C6H12O6')
        prop2 = core.SpeciesTypeProperty(
            property = 'charge',
            value_type = kbOnt['WC:integer'],
            value = '-3')
        met1 = core.MetaboliteSpeciesType(properties=[prop1, prop2])
        met2 = core.MetaboliteSpeciesType()

        self.assertEqual(met1.get_empirical_formula(), chem.EmpiricalFormula('C6H12O6'))
        self.assertEqual(met1.get_charge(), -3)
        self.assertAlmostEqual(met1.get_mol_wt(), 180.156)

        with self.assertRaises(ValueError):
            met2.get_empirical_formula()
            met2.get_charge()
            met2.get_mol_wt()

    def test_get_structure(self):
        speciesTypeProperties = core.SpeciesTypeProperty(
            property = 'structure',
            value_type = kbOnt['WC:string'],
            value = (
                'InChI=1S'
                '/C10H14N5O7P'
                '/c11-8-5-9(13-2-12-8)15(3-14-5)10-7(17)6(16)4(22-10)1-21-23(18,19)20'
                '/h2-4,6-7,10,16-17H,1H2,(H2,11,12,13)(H2,18,19,20)'
                '/p-2/t4-,6-,7-,10-'
                '/m1'
                '/s1'))
        met = core.MetaboliteSpeciesType(properties = [speciesTypeProperties])
        self.assertEqual(met.calc_structure(), speciesTypeProperties.value)
        self.assertEqual(met.calc_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O7P'))
        self.assertEqual(met.calc_charge(), -2)
        self.assertAlmostEqual(met.get_mol_wt(), 345.20530, places=4)

        speciesTypeProperties = core.SpeciesTypeProperty(
            property = 'structure',
            value_type = kbOnt['WC:string'],
            value = ('[H]O[C@@]1([H])[C@@]([H])(O[C@]([H])(C([H])([H])OP([O-])([O-])=O)[C@@]1([H])O[H])N1C([H])=NC2=C(N=C([H])N=C12)N([H])[H]'))
        met = core.MetaboliteSpeciesType(properties = [speciesTypeProperties])
        self.assertEqual(met.calc_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O7P'))
        self.assertEqual(met.calc_charge(), -2)
        self.assertAlmostEqual(met.get_mol_wt(), 345.20530, places=4)
        
class ReactionAndRelatedClassesTestCase(unittest.TestCase):

    def setUp(self):
        self.cell_1 = cell_1 = core.Cell()
        self.compartment_1 = compartment_1 = core.Compartment(cell=cell_1, id='c')
        self.species_type_1 = species_type_1 = core.MetaboliteSpeciesType(id='species_type_1')
        self.species_type_2 = species_type_2 = core.MetaboliteSpeciesType(id='species_type_2')
        self.species_1 = species_1 = core.Species(
            species_type=species_type_1, compartment=compartment_1)
        self.species_2 = species_2 = core.Species(
            species_type=species_type_2, compartment=compartment_1)
        self.participant_1 = participant_1 = core.SpeciesCoefficient(
            species=species_1, coefficient=1)
        self.participant_2 = participant_2 = core.SpeciesCoefficient(
            species=species_2, coefficient=1)

        self.observable_expression_1 = observable_expression_1 = core.ObservableExpression(
            expression='{} + {}'.format(species_1.id(), species_2.id()),
            species=[species_1, species_2]
        )

        self.observable_1 = observable_1 = core.Observable(
            id='obs1', expression=observable_expression_1
        )

        self.parameter_1 = parameter_1 = core.Parameter(
            id='p1',
            name='test_parameter1',
            value=0.7,
            error=0.01,
            units=unit_registry.parse_units('s^-1')
        )

        self.parameter_2 = parameter_2 = core.Parameter(
            id='p2',
            name='test_parameter2',
            value=2.,
            error=0.1,
            units=unit_registry.parse_units('M')
        )

        self.parameter_3 = parameter_3 = core.Parameter(
            id='p3',
            name='test_parameter3',
            value=2.3,
            error=0.15,
            units=unit_registry.parse_units('M'),
        )

        self.reaction_1 = reaction_1 = core.Reaction(
            id='reaction_1',
            name='test_reaction',
            cell=cell_1,
            participants=[participant_1, participant_2],
            reversible=False)

        self.rate_law_expression_1 = rate_law_expression_1 = core.RateLawExpression(
            expression=species_1.id(), species = [species_1]
        )

        self.rate_law_1 = rate_law_1 = core.RateLaw(
            reaction=reaction_1,
            direction=core.RateLawDirection.forward,
            expression=rate_law_expression_1,
            units=unit_registry.parse_units('s^-1')
        )

        self.reaction_2 = reaction_2 = core.Reaction(
            id='reaction_2',
            name='test_reaction2',
            cell=cell_1,
            participants=[participant_1, participant_2],
            reversible=False)

        self.rate_law_expression_2 = rate_law_expression_2 = core.RateLawExpression(
            expression='p1 * species_type_1[c] * species_type_2[c] / ( p2 + ( obs1 ^ 2 / p3 ) )',
            species=[species_1, species_2],
            observables=[observable_1],
            parameters=[parameter_1, parameter_2, parameter_3]
        )

        self.rate_law_2 = rate_law_2 = core.RateLaw(
            reaction=reaction_2,
            direction=core.RateLawDirection.backward,
            expression=rate_law_expression_2
        )

        self.objects = {
            core.Compartment: {
                compartment_1.id: compartment_1
            },
            core.MetaboliteSpeciesType: {
                species_type_1.id: species_type_1,
                species_type_2.id: species_type_2
            },
            core.Species: {
                species_1.id(): species_1,
                species_2.id(): species_2
            },
            core.Parameter: {
                parameter_1.id: parameter_1,
                parameter_2.id: parameter_2,
                parameter_3.id: parameter_3
            },
            core.Observable: {
                observable_1.id: observable_1,
            }
        }

    # Junk tests
    def test_Reaction(self):
        self.assertEqual(self.reaction_1.id, 'reaction_1')
        self.assertEqual(self.reaction_1.name, 'test_reaction')
        self.assertEqual(self.reaction_1.cell, self.cell_1)
        self.assertEqual(self.reaction_1.participants, [self.participant_1, self.participant_2])
        self.assertEqual(self.reaction_1.reversible, 0)

    def test_RateLawExpression(self):
        self.assertEqual(self.rate_law_expression_1.serialize(), 'species_type_1[c]')

    def test_RateLaw(self):
        self.assertEqual(self.rate_law_1.direction, core.RateLawDirection.forward)
        self.assertEqual(self.rate_law_1.expression, self.rate_law_expression_1)
        self.assertEqual(self.rate_law_1.gen_id(), 'reaction_1_forward')

        self.assertEqual(self.rate_law_2.direction, core.RateLawDirection.backward)
        self.assertEqual(self.rate_law_2.expression, self.rate_law_expression_2)
        self.assertIn(self.rate_law_2.gen_id(), 'reaction_2_backward')

    # Junk test
    def test_Parameter(self):
        self.assertEqual(self.parameter_1.id, 'p1')
        self.assertEqual(self.parameter_2.name, 'test_parameter2')
        self.assertEqual(self.parameter_3.value, 2.3)
        self.assertEqual(self.parameter_3.error, 0.15)
        self.assertEqual(self.parameter_3.units, unit_registry.parse_units('M'))
        self.assertEqual(self.parameter_3.references, [])
        self.assertEqual(self.parameter_3.identifiers, [])

    def test_deserialize_RateLawExpression(self):

        # add RateLawExpression to self.objects
        rle_1, error = core.RateLawExpression().deserialize(
            value='species_type_1[c]', objects=self.objects)
        self.assertTrue(error is None)
        self.assertEqual(rle_1.species, [self.species_1])
        rle_2, error = core.RateLawExpression().deserialize(
            value='p1 * species_type_1[c] * species_type_2[c] / ( p2 + ( obs1 ** 2 / p3 ) )',
            objects=self.objects)
        self.assertTrue(error is None)
        self.assertEqual(set(rle_2.species), set([self.species_1, self.species_2]))
        self.assertEqual(rle_2.observables, [self.observable_1])
        self.assertEqual(set(rle_2.parameters), set([self.parameter_1, self.parameter_2, self.parameter_3]))

        # RateLawExpression is in self.objects, and value is in self.objects[RateLawExpression]
        rle_3, error = core.RateLawExpression().deserialize(
            value=self.species_1.id(), objects=self.objects)
        self.assertTrue(error is None)
        self.assertEqual(rle_3.species, [self.species_1])
        self.assertEqual(rle_1, rle_3)

        # Species.deserialize fails
        value = 'not_species_id[x]'
        obj, error = core.RateLawExpression().deserialize(value=value, objects=self.objects)
        self.assertTrue(obj is None)

# Done
class ComplexSpeciesTypeTestCase(unittest.TestCase):

    def setUp(self):

        self.complex1  = core.ComplexSpeciesType()
        self.complex2  = core.ComplexSpeciesType()

        speciesProps1 = core.SpeciesTypeProperty(
            property = 'structure',
            value = 'InChI=1S/C8H7NO3/c10-6-1-4-5(2-7(6)11)9-3-8(4)12/h1-2,8-9,12H,3H2',
            value_type = kbOnt['WC:string'])
        speciesProps2 = core.SpeciesTypeProperty(
            property = 'structure',
            value = 'InChI=1S/Zn/q+2',
            value_type = kbOnt['WC:string'])


        self.cofactor1 = core.MetaboliteSpeciesType(id='1cofactor1',
                                               properties = [speciesProps1])
        self.cofactor2 = core.MetaboliteSpeciesType(id='cofactor2',
                                               properties = [speciesProps2])

        # Add subunit composition: (2) cofactor1 + (3) cofactor2 ==> complex1
        species_type_coeff1 = core.SpeciesTypeCoefficient(
            species_type=self.cofactor1, coefficient=2)
        species_type_coeff2 = core.SpeciesTypeCoefficient(
            species_type=self.cofactor2, coefficient=3)
        self.complex1.subunits = [species_type_coeff1, species_type_coeff2]

        # Add subunit composition: (1) cofactor1 + (1) cofactor2 ==> complex1
        species_type_coeff1 = core.SpeciesTypeCoefficient(
            species_type=self.cofactor1, coefficient=1)
        species_type_coeff2 = core.SpeciesTypeCoefficient(
            species_type=self.cofactor2, coefficient=1)
        self.complex2.subunits = [species_type_coeff1, species_type_coeff2]

    def tearDown(self):
        pass

    def test_get_charge(self):
        self.assertEqual(self.complex1.get_charge(), 6)
        self.assertEqual(self.complex2.get_charge(), 2)

    def test_get_mol_wt(self):
        self.assertAlmostEqual(self.complex1.get_mol_wt(),
                               (2*self.cofactor1.get_mol_wt() + 3*self.cofactor2.get_mol_wt()))

        self.assertAlmostEqual(self.complex2.get_mol_wt(),
                               (self.cofactor1.get_mol_wt() + self.cofactor2.get_mol_wt()))

    def test_get_empirical_formula(self):
        self.assertEqual(self.complex1.get_empirical_formula(),
                         chem.EmpiricalFormula('C16H14N2O6Zn3'))

        self.assertEqual(self.complex2.get_empirical_formula(),
                         chem.EmpiricalFormula('C8H7N1O3Zn1'))


#Done
class SpeciesCoefficientTestCase(unittest.TestCase):
    def test_constructor(self):
        comp = core.Compartment(id='c')
        met = core.MetaboliteSpeciesType(id='met')

        spec = core.Species(species_type=met, compartment=comp)
        spec_coeff = core.SpeciesCoefficient(species=spec, coefficient=3)

        self.assertEqual(spec_coeff.species.species_type.id, 'met')
        self.assertEqual(spec_coeff.species.compartment.id, 'c')
        self.assertEqual(spec_coeff.coefficient, 3)

    def test_serialize(self):
        comp = core.Compartment(id='c')
        met = core.MetaboliteSpeciesType(id='met')

        spec = core.Species(species_type=met, compartment=comp)
        spec_coeff = core.SpeciesCoefficient(species=spec, coefficient=3)

        self.assertEqual(spec_coeff.serialize(), '(3) met[c]')
        self.assertEqual(core.SpeciesCoefficient._serialize(
            species=spec, coefficient=3), '(3) met[c]')
        self.assertEqual(core.SpeciesCoefficient._serialize(
            species=spec, coefficient=1), 'met[c]')
        self.assertEqual(core.SpeciesCoefficient._serialize(
            species=spec, coefficient=2000), '(2.000000e+03) met[c]')
        self.assertEqual(core.SpeciesCoefficient._serialize(
            species=spec, coefficient=3, show_compartment=False), '(3) met')
        self.assertEqual(core.SpeciesCoefficient._serialize(
            species=spec, coefficient=-1), '(-1) met[c]')
        self.assertEqual(core.SpeciesCoefficient._serialize(
            species=spec, coefficient=-1, show_coefficient_sign=False), 'met[c]')

    def test_deserialize(self):
        comp = core.Compartment(id='c')
        dna = core.DnaSpeciesType(id='dna')
        met = core.MetaboliteSpeciesType(id='2met')

        spec = core.Species(species_type=dna, compartment=comp)

        objects = {
            core.Compartment: {
                'c': comp,
            },
            core.DnaSpeciesType: {
                'dna': dna,
            },
            core.MetaboliteSpeciesType: {
                '2met': met,
            },
            core.Species: {
                'dna[c]': spec,
            },
        }

        attr = core.Reaction.participants

        result = core.SpeciesCoefficient.deserialize(
            attr, '(3) dna[c]', objects)
        self.assertEqual(result[0].species, spec)
        self.assertEqual(result[0].coefficient, 3)
        self.assertEqual(result[1], None)
        self.assertEqual(len(objects[core.Species]), 1)
        self.assertEqual(len(objects[core.SpeciesCoefficient]), 1)

        result2 = core.SpeciesCoefficient.deserialize(
            attr, '(3) dna[c]', objects)
        self.assertEqual(result2[0], result[0])
        self.assertEqual(result2[1], None)
        self.assertEqual(len(objects[core.Species]), 1)
        self.assertEqual(len(objects[core.SpeciesCoefficient]), 1)

        result = core.SpeciesCoefficient.deserialize(
            attr, '(-2) dna[c]', objects)
        self.assertEqual(result[0].species, spec)
        self.assertEqual(result[0].coefficient, -2)
        self.assertEqual(result[1], None)
        self.assertEqual(len(objects[core.Species]), 1)
        self.assertEqual(len(objects[core.SpeciesCoefficient]), 2)

        result = core.SpeciesCoefficient.deserialize(attr, 'dna[c]', objects)
        self.assertEqual(result[0].species, spec)
        self.assertEqual(result[0].coefficient, 1)
        self.assertEqual(result[1], None)
        self.assertEqual(len(objects[core.Species]), 1)
        self.assertEqual(len(objects[core.SpeciesCoefficient]), 3)

        result = core.SpeciesCoefficient.deserialize(attr, '2met[c]', objects)
        self.assertEqual(result[0].species.species_type, met)
        self.assertEqual(result[0].species.compartment, comp)
        self.assertEqual(result[0].coefficient, 1)
        self.assertEqual(result[1], None)
        self.assertEqual(len(objects[core.Species]), 2)
        self.assertEqual(len(objects[core.SpeciesCoefficient]), 4)

        result = core.SpeciesCoefficient.deserialize(attr, 'dna2[c]', objects)
        self.assertEqual(result[0], None)
        self.assertNotEqual(result[1], None)

        result = core.SpeciesCoefficient.deserialize(attr, 'dna', objects)
        self.assertEqual(result[0], None)
        self.assertNotEqual(result[1], None)

        result = core.SpeciesCoefficient.deserialize(
            attr, 'dna', objects, compartment=comp)
        self.assertEqual(result[0].species.species_type, dna)
        self.assertEqual(result[0].species.compartment, comp)
        self.assertEqual(result[0].coefficient, 1)
        self.assertEqual(result[1], None)

        result = core.SpeciesCoefficient.deserialize(
            attr, '(2) dna', objects, compartment=comp)
        self.assertEqual(result[0].species.species_type, dna)
        self.assertEqual(result[0].species.compartment, comp)
        self.assertEqual(result[0].coefficient, 2)
        self.assertEqual(result[1], None)

        result = core.SpeciesCoefficient.deserialize(
            attr, '(-3) dna', objects, compartment=comp)
        self.assertEqual(result[0].species.species_type, dna)
        self.assertEqual(result[0].species.compartment, comp)
        self.assertEqual(result[0].coefficient, -3)
        self.assertEqual(result[1], None)


#Done
class SpeciesTypeCoefficientTestCase(unittest.TestCase):
    def test_constructor(self):

        met = core.MetaboliteSpeciesType(id='met')
        species_type_coeff = core.SpeciesTypeCoefficient(species_type=met, coefficient=3)

        self.assertEqual(species_type_coeff.species_type.id, 'met')
        self.assertEqual(species_type_coeff.coefficient, 3)

    def test_serialize(self):

        met = core.MetaboliteSpeciesType(id='met')
        species_type_coeff = core.SpeciesTypeCoefficient(species_type=met, coefficient=3)

        self.assertEqual(species_type_coeff.serialize(), '(3) met')
        self.assertEqual(core.SpeciesTypeCoefficient._serialize(
            species_type=met, coefficient=3), '(3) met')
        self.assertEqual(core.SpeciesTypeCoefficient._serialize(
            species_type=met, coefficient=1), 'met')
        self.assertEqual(core.SpeciesTypeCoefficient._serialize(
            species_type=met, coefficient=2000), '(2.000000e+03) met')

    def test_deserialize(self):
    
        met1 = core.MetaboliteSpeciesType(id='1met1') 
        met2 = core.MetaboliteSpeciesType(id='met2') 

        objects = {
            core.MetaboliteSpeciesType: {
                '1met1': met1,
                'met2': met2,
            },
        }        

        attr = core.ComplexSpeciesType.subunits

        result = core.SpeciesTypeCoefficient.deserialize(attr, '1met1 + met2', objects)
        self.assertEqual(sorted(['{}:{}'.format(i.species_type.id, i.coefficient) for i in result[0]]), 
            sorted(['1met1:1.0', 'met2:1.0']))
        self.assertEqual(result[1], None)

        result = core.SpeciesTypeCoefficient.deserialize(attr, '(0) 1met1 + (1) met2', objects)
        self.assertEqual(sorted(['{}:{}'.format(i.species_type.id, i.coefficient) for i in result[0]]), 
            sorted(['1met1:0.0', 'met2:1.0']))
        self.assertEqual(result[1], None)

#Done
class SubunitAttributeTestCase(unittest.TestCase):
    def test_SubunitAttribute(self):
        compart1 = core.Compartment(id='c')

        met1 = core.MetaboliteSpeciesType(id='met1')
        dna1 = core.DnaSpeciesType(id='dna1')
        complex1 = core.ComplexSpeciesType(id='complex1')

        species1 = core.Species(species_type=complex1, compartment=compart1)

        species_type_coeff1 = core.SpeciesTypeCoefficient(
            species_type=met1, coefficient=2)
        species_type_coeff2 = core.SpeciesTypeCoefficient(
            species_type=dna1, coefficient=3)
        species_type_coeff3 = core.SpeciesTypeCoefficient(
            species_type=complex1, coefficient=5)

        self.assertEqual(
            core.SubunitAttribute().serialize(subunits=[]), '')
        self.assertEqual(core.SubunitAttribute().serialize(subunits=[species_type_coeff1]),
                         '(2) met1')
        self.assertEqual(core.SubunitAttribute().serialize(subunits=[species_type_coeff1, species_type_coeff2]),
                         '(3) dna1 + (2) met1')
        self.assertEqual(core.SubunitAttribute().serialize(subunits=[species_type_coeff1, species_type_coeff2, species_type_coeff3]),
                         '(5) complex1 + (3) dna1 + (2) met1')

        objects = {
            core.DnaSpeciesType: {
                'dna1': dna1
            },
            core.MetaboliteSpeciesType: {
                'met1': met1
            },
            core.ComplexSpeciesType: {
                'complex1': complex1
            },
        }

        result = core.SubunitAttribute().deserialize(
            value='met1 + (2) dna1', objects=objects)
        self.assertEqual(result[0][0].species_type, met1)
        self.assertEqual(result[0][1].species_type, dna1)
        self.assertEqual(result[0][0].coefficient, 1)
        self.assertEqual(result[0][1].coefficient, 2)
        self.assertEqual(result[0][0].species_type.id, 'met1')
        self.assertEqual(result[0][1].species_type.id, 'dna1')
        self.assertEqual(result[1], None)

        result = core.SubunitAttribute().deserialize(
            value='(2) met1 + (7) complex1', objects=objects)
        self.assertEqual(result[0][0].species_type, met1)
        self.assertEqual(result[0][1].species_type, complex1)
        self.assertEqual(result[0][0].coefficient, 2)
        self.assertEqual(result[0][1].coefficient, 7)
        self.assertEqual(result[0][0].species_type.id, 'met1')
        self.assertEqual(result[0][1].species_type.id, 'complex1')
        self.assertEqual(result[1], None)

        result = core.SubunitAttribute().deserialize(
            value='[c]met1 + (2) dna1', objects=objects)
        self.assertEqual(result[0], None)
        self.assertEqual(
            result[1].messages[0], 'Incorrectly formatted participants: [c]met1 + (2) dna1')


# Organized + cover + passes
class ReactionParticipantAttributeTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.compart1 = core.Compartment(id='c')
        cls.compart2 = core.Compartment(id='m')

        cls.met1 = core.MetaboliteSpeciesType(id='1met1')
        cls.met2 = core.MetaboliteSpeciesType(id='met2')
        cls.complex1 = core.ComplexSpeciesType(id='complex1')

        cls.species1 = core.Species(species_type=cls.met1, compartment=cls.compart1)
        cls.species2 = core.Species(species_type=cls.met2, compartment=cls.compart1)
        cls.species3 = core.Species(species_type=cls.complex1, compartment=cls.compart1)
        cls.species4 = core.Species(species_type=cls.complex1, compartment=cls.compart2)

        cls.species_coeff1 = core.SpeciesCoefficient(
            species=cls.species1, coefficient=-2)
        cls.species_coeff2 = core.SpeciesCoefficient(
            species=cls.species2, coefficient=-3)
        cls.species_coeff3 = core.SpeciesCoefficient(
            species=cls.species3, coefficient=5)
        cls.species_coeff4 = core.SpeciesCoefficient(
            species=cls.species4, coefficient=7)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_serialize(self):

        self.assertEqual(
            core.ReactionParticipantAttribute().serialize(participants=[]), '')
        self.assertEqual(core.ReactionParticipantAttribute().serialize(participants=[self.species_coeff1]),
                         '[c]: (2) 1met1 ==> ')
        self.assertEqual(core.ReactionParticipantAttribute().serialize(participants=[self.species_coeff1, self.species_coeff2]),
                         '[c]: (2) 1met1 + (3) met2 ==> ')
        self.assertEqual(core.ReactionParticipantAttribute().serialize(participants=[self.species_coeff1, self.species_coeff2, self.species_coeff3]),
                         '[c]: (2) 1met1 + (3) met2 ==> (5) complex1')
        self.assertEqual(core.ReactionParticipantAttribute().serialize(participants=[self.species_coeff1, self.species_coeff2, self.species_coeff4]),
                         '(2) 1met1[c] + (3) met2[c] ==> (7) complex1[m]')

    def test_deserialize(self):

        objects = {
            core.DnaSpeciesType: {},
            core.MetaboliteSpeciesType: {
                '1met1': self.met1, 'met2': self.met2
            },
            core.ComplexSpeciesType: {
                'complex1': self.complex1
            },
            core.Compartment: {
                'c': self.compart1, 'm': self.compart2
            },
            core.Species: {
                '1met1[c]': self.species1, 'met2[c]': self.species2, 'complex1[c]': self.species3, 'complex[m]': self.species4
            },
        }

        result = core.ReactionParticipantAttribute().deserialize(
            value='[c]: 1met1 ==> met2', objects=objects)
        self.assertEqual(result[0][0].species.species_type, self.met1)
        self.assertEqual(result[0][1].species.species_type, self.met2)
        self.assertEqual(result[0][0].coefficient, -1)
        self.assertEqual(result[0][1].coefficient,  1)
        self.assertEqual(result[0][0].species.compartment, self.compart1)
        self.assertEqual(result[0][1].species.compartment, self.compart1)
        self.assertEqual(result[0][0].species.id(), '1met1[c]')
        self.assertEqual(result[0][1].species.id(), 'met2[c]')
        self.assertEqual(result[1], None)

        result = core.ReactionParticipantAttribute().deserialize(
            value='[c]: 1met1 ==> ', objects=objects)
        self.assertEqual(result[0][0].species.species_type, self.met1)
        self.assertEqual(result[0][0].coefficient, -1)
        self.assertEqual(result[0][0].species.compartment, self.compart1)
        self.assertEqual(result[0][0].species.id(), '1met1[c]')
        self.assertEqual(result[1], None)

        result = core.ReactionParticipantAttribute().deserialize(
            value='[c]: ==> met2', objects=objects)
        self.assertEqual(result[0][0].species.species_type, self.met2)
        self.assertEqual(result[0][0].coefficient,  1)
        self.assertEqual(result[0][0].species.compartment, self.compart1)
        self.assertEqual(result[0][0].species.id(), 'met2[c]')
        self.assertEqual(result[1], None)

        result = core.ReactionParticipantAttribute().deserialize(
            value='(2) 1met1[c] + (3) met2[c] ==> (7) complex1[m]', objects=objects)
        self.assertEqual(result[0][0].species.species_type, self.met1)
        self.assertEqual(result[0][1].species.species_type, self.met2)
        self.assertEqual(result[0][2].species.species_type, self.complex1)
        self.assertEqual(result[0][0].coefficient, -2)
        self.assertEqual(result[0][1].coefficient, -3)
        self.assertEqual(result[0][2].coefficient, 7.0)
        self.assertEqual(result[0][0].species.compartment, self.compart1)
        self.assertEqual(result[0][1].species.compartment, self.compart1)
        self.assertEqual(result[0][2].species.compartment, self.compart2)
        self.assertEqual(result[0][0].species.id(), '1met1[c]')
        self.assertEqual(result[0][1].species.id(), 'met2[c]')
        self.assertEqual(result[0][2].species.id(), 'complex1[m]')
        self.assertEqual(result[1], None)

        result = core.ReactionParticipantAttribute().deserialize(
            value='met2[c] ==>', objects=objects)
        self.assertEqual(result[0], None)
        self.assertEqual(
            result[1].messages[0], 'Incorrectly formatted participants: met2[c] ==>')

        result = core.ReactionParticipantAttribute().deserialize(
            value='==> 1met1[c]', objects=objects)
        self.assertEqual(result[0], None)
        self.assertEqual(
            result[1].messages[0], 'Incorrectly formatted participants: ==> 1met1[c]')

# Organized + cover + passes
class ObservableExpressionTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.cell  = core.Cell()
        cls.comp1 = core.Compartment(id='c')
        cls.dna1  = core.DnaSpeciesType(id='dna1')
        cls.met1  = core.MetaboliteSpeciesType(id='met1')

        cls.species1 = core.Species(species_type=cls.met1, compartment=cls.comp1)
        cls.species2 = core.Species(species_type=cls.dna1, compartment=cls.comp1)

        cls.exp1 = core.ObservableExpression(expression='2 * met1[c] + 3.3 * dna1[c]', species=[cls.species1, cls.species2])
        cls.observable1 = core.Observable(cell=cls.cell, id='obs1', expression=cls.exp1)
        cls.exp2 = core.ObservableExpression(expression='met1[c] / obs1', species=[cls.species1], observables=[cls.observable1])

    @classmethod
    def tearDownClass(cls):
        pass

    def test_serialize(self):

        self.assertEqual(self.exp1.serialize(), '2 * met1[c] + 3.3 * dna1[c]')
        self.assertEqual(self.exp2.serialize(), 'met1[c] / obs1')

    def test_deserialize(self):

        objects = {
            core.Compartment: {
                'c': self.comp1
            },
            core.MetaboliteSpeciesType: {
                'met1': self.met1
            },
            core.DnaSpeciesType: {
                'dna1': self.dna1
            },
            core.Species: {
                'met1[c]': self.species1, 'dna1[c]': self.species2
            },
            core.Observable: {
                'obs1': self.observable1
            }
        }

        result1 = core.ObservableExpression().deserialize(
            value='2 * met1[c] + 3.3 * dna1[c]', objects=objects)
        result2 = core.ObservableExpression().deserialize(
            value='met1[c] / obs1', objects=objects)

        self.assertEqual(result1[0].expression, '2 * met1[c] + 3.3 * dna1[c]')
        self.assertEqual(set([i.species_type.id for i in result1[0].species]), set(['met1', 'dna1']))
        self.assertEqual(set([i.compartment.id for i in result1[0].species]), set(['c', 'c']))
        self.assertEqual(result1[1], None)
        self.assertEqual(result2[0].expression, 'met1[c] / obs1')
        self.assertEqual(result2[0].species[0].species_type.id, 'met1')
        self.assertEqual(result2[0].observables[0].id, 'obs1')
        self.assertEqual(result2[1], None)

# Organized + cover + passes (deseralize uses ObservableExpression's method - junk test)
class ObservableTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.cell  = core.Cell()
        cls.comp1 = core.Compartment(id='c')
        cls.met1  = core.MetaboliteSpeciesType(id='met1')
        cls.dna1  = core.DnaSpeciesType(id='dna1')

        cls.species1 = core.Species(species_type=cls.met1, compartment=cls.comp1)
        cls.species2 = core.Species(species_type=cls.dna1, compartment=cls.comp1)

        cls.exp1 = core.ObservableExpression(expression='2 * met1[c] + 3.3 * dna1[c]', species=[cls.species1, cls.species2])
        cls.observable1 = core.Observable(cell=cls.cell, id='obs1', expression=cls.exp1)

        cls.exp2 = core.ObservableExpression(expression='met1[c] / obs1', species=[cls.species1], observables=[cls.observable1])
        cls.observable2 = core.Observable(cell=cls.cell, id='obs2', expression=cls.exp2)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_observables(self):

        self.assertEqual(self.cell.observables.get_one(id='obs1').expression.expression, '2 * met1[c] + 3.3 * dna1[c]')
        self.assertEqual(set([i.species_type.id for i in self.cell.observables.get_one(id='obs1').expression.species]), set(['met1', 'dna1']))
        self.assertEqual(self.cell.observables.get_one(id='obs1').expression.observables, [])
        self.assertEqual(self.cell.observables.get_one(id='obs2').expression.observables[0], self.observable1)

# Organized + cover + passes
class ValidatorTestCase(unittest.TestCase):
    def test(self):
        kb = core.KnowledgeBase(id='kb', name='test kb', version='0.0.1', wc_kb_version='0.0.1')
        self.assertEqual(core.Validator().run(kb), None)

        kb.id = ''
        self.assertNotEqual(core.Validator().run(kb), None)


class SpeciesTypePropertyTestCase(unittest.TestCase):

    def test_get_value(self):

        cell1 = core.Cell(id='cell1')
        kb = core.KnowledgeBase(cell = cell1)
        c = core.Compartment(id='c', cell=cell1)
        met = core.MetaboliteSpeciesType(id='met1', cell=cell1)

        stp1 = core.SpeciesTypeProperty(id='stp1', species_type=met, property='whatever1', value='True', value_type = kbOnt['WC:boolean'])
        stp2 = core.SpeciesTypeProperty(id='stp2', species_type=met, property='whatever2', value='check_str', value_type = kbOnt['WC:string'])
        stp3 = core.SpeciesTypeProperty(id='stp3', species_type=met, property='whatever3', value='3', value_type = kbOnt['WC:integer'])
        stp4 = core.SpeciesTypeProperty(id='stp4', species_type=met, property='whatever4', value='4.6', value_type = kbOnt['WC:float'])
        stp6 = core.SpeciesTypeProperty(id='stp6', species_type=met, property='whatever7', value='raise_test', value_type= 'raise_test')

        self.assertEqual(met.properties.get_one(id='stp1').get_value(), True)
        self.assertEqual(met.properties.get_one(id='stp2').get_value(), 'check_str')
        self.assertEqual(met.properties.get_one(id='stp3').get_value(), int(3))
        self.assertEqual(met.properties.get_one(id='stp4').get_value(), 4.6)

        with self.assertRaises(ValueError):
            met.properties.get_one(id='stp6').get_value()
