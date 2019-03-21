""" Tests of the knowledge base schema for prokaryotes

:Author: Balazs Szigeti <balazs.szigeti@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Author: Bilal Shaikh <bilal.shaikh@columbia.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Yin Hoon Chew <yinhoon.chew@mssm.edu>
:Date: 2018-02-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_kb import core, prokaryote_schema
from wc_utils.util import chem
import Bio.Alphabet
import Bio.Seq
import Bio.SeqUtils
import mendeleev
import os
import shutil
import tempfile
import unittest
import pdb


class RnaSpeciesTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_dirname = tempfile.mkdtemp()
        self.sequence_path = os.path.join(self.tmp_dirname, 'test_seq.fasta')
        with open(self.sequence_path, 'w') as f:
            f.write('>dna1\nACGTACGTACGTACG\n'
                    '>dna2\nA\n'
                    '>dna3\nC\n'
                    '>dna4\nG\n'
                    '>dna5\nT\n'
                    '>dna6\nAAAA\n'
                    '>dna7\nAACCGGTT\n')

    def tearDown(self):
        shutil.rmtree(self.tmp_dirname)

    # Taken acre of by obj_model?
    def test_constructor(self):
        dna1 = core.DnaSpeciesType(id='dna1', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=15)
        rna1 = prokaryote_schema.RnaSpeciesType(id='rna1', name='rna1', transcription_units=[
                                   tu1], type=1, half_life=2)

        # make sure that only TU can be created that have valid length
        # These should throw errors:
        #tu2 = prokaryote_schema.TranscriptionUnitLocus(id='tu1', polymer=dna1, start=1, end=20)
        #tu2 = prokaryote_schema.TranscriptionUnitLocus(id='tu1', polymer=dna1, start=-3, end=20)

        self.assertEqual(rna1.id, 'rna1')
        self.assertEqual(rna1.name, 'rna1')
        self.assertEqual(rna1.transcription_units, [tu1])
        self.assertEqual(rna1.type, 1)
        self.assertEqual(rna1.half_life, 2)

    def test_get_seq(self):

        dna1 = core.DnaSpeciesType(id='dna1', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=15)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_seq(), dna1.get_seq().transcribe())

        dna1 = core.DnaSpeciesType(id='dna2', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=1)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_seq(), dna1.get_seq().transcribe())

        dna1 = core.DnaSpeciesType(id='dna7', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=8)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_seq(), dna1.get_seq().transcribe())

    def test_get_empirical_formula(self):

        dna1 = core.DnaSpeciesType(id='dna2', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=1)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O7P'))

        dna1 = core.DnaSpeciesType(id='dna3', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=1)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_empirical_formula(),
                         chem.EmpiricalFormula('C9H12N3O8P'))

        dna1 = core.DnaSpeciesType(id='dna4', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=1)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_empirical_formula(),
                         chem.EmpiricalFormula('C10H12N5O8P'))

        dna1 = core.DnaSpeciesType(id='dna5', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=1)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_empirical_formula(),
                         chem.EmpiricalFormula('C9H11N2O9P'))

        dna1 = core.DnaSpeciesType(id='dna6', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=2)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_empirical_formula(),
                         chem.EmpiricalFormula('C20H23N10O13P2'))

    def test_get_charge(self):

        dna1 = core.DnaSpeciesType(id='dna6', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=1)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_charge(), -2)

        dna1 = core.DnaSpeciesType(id='dna6', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=2)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(rna1.get_charge(), -3)

    def test_get_mol_wt(self):

        dna1 = core.DnaSpeciesType(id='dna7', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=1)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(rna1.get_seq()) \
            - (rna1.get_len() + 1) * mendeleev.element('H').atomic_weight
        self.assertAlmostEqual(rna1.get_mol_wt(), exp_mol_wt, places=1)

        dna1 = core.DnaSpeciesType(id='dna7', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=3, end=3)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(rna1.get_seq()) \
            - (rna1.get_len() + 1) * mendeleev.element('H').atomic_weight
        self.assertAlmostEqual(rna1.get_mol_wt(), exp_mol_wt, places=1)

        dna1 = core.DnaSpeciesType(id='dna7', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=5, end=5)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(rna1.get_seq()) \
            - (rna1.get_len() + 1) * mendeleev.element('H').atomic_weight
        self.assertAlmostEqual(rna1.get_mol_wt(), exp_mol_wt, places=1)

        # Adding cases that have ,multiple nucleotides
        dna1 = core.DnaSpeciesType(id='dna7', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=8)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(rna1.get_seq()) \
            - (rna1.get_len() + 1) * mendeleev.element('H').atomic_weight
        self.assertAlmostEqual(rna1.get_mol_wt(), exp_mol_wt, places=1)

        dna1 = core.DnaSpeciesType(id='dna1', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=15)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        exp_mol_wt = \
            + Bio.SeqUtils.molecular_weight(rna1.get_seq()) \
            - (rna1.get_len() + 1) * mendeleev.element('H').atomic_weight
        self.assertAlmostEqual(rna1.get_mol_wt(), exp_mol_wt, places=1)


class ProteinSpeciesTypeTestCase(unittest.TestCase):

    def setUp(self):
        # Mycoplasma Genintalium Genome
        dna1 = core.DnaSpeciesType(id='chromosome', sequence_path='tests/fixtures/seq.fna')

        cell1 = dna1.cell = core.Cell()
        cell1.knowledge_base = core.KnowledgeBase(
            translation_table=4)  # Table 4 is for mycoplasma

        # MPN001
        gene1 = prokaryote_schema.GeneLocus(id='gene1', cell=cell1,
                               polymer=dna1, start=692, end=1834)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', genes=[gene1], polymer=dna1)
        self.prot1 = prokaryote_schema.ProteinSpeciesType(
            id='prot1', gene=gene1, cell=cell1)

        # MPN011
        gene2 = prokaryote_schema.GeneLocus(id='gene2', cell=cell1, polymer=dna1,
                               start=12838, end=13533, strand=core.PolymerStrand.negative)
        tu2 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu2', genes=[gene2], polymer=dna1)
        self.prot2 = prokaryote_schema.ProteinSpeciesType(
            id='prot2', gene=gene2, cell=cell1)

    def test_get_seq(self):
        # Use translation table 4 since example genes are from
        # Mycoplasma genitallium

        # MPN001
        self.assertEqual(self.prot1.get_seq()[0:10], 'MKVLINKNEL')
        self.assertEqual(self.prot1.get_seq()[-10:], 'ELKEILVPSK')

        # MPN011
        self.assertEqual(self.prot2.get_seq()[0:10], 'MKFKFLLTPL')
        self.assertEqual(self.prot2.get_seq()[-10:], 'LFRYLVYLIE')

    def test_get_empirical_formula(self):
        # MPN001
        self.assertEqual(self.prot1.get_empirical_formula(),
                         chem.EmpiricalFormula('C1980H3146N510O596S7'))
        # MPN011
        self.assertEqual(self.prot2.get_empirical_formula(),
                         chem.EmpiricalFormula('C1246H1928N306O352S3'))

    def test_get_mol_wt(self):
        # MPN001
        self.assertAlmostEqual(self.prot1.get_mol_wt(), 43856.342, delta=0.3)
        # MNP011
        self.assertAlmostEqual(self.prot2.get_mol_wt(), 26923.100, delta=0.3)

    def test_get_charge(self):
        self.assertEqual(self.prot1.get_charge(), 1)

        self.assertEqual(self.prot2.get_charge(), 12)


class TranscriptionUnitLocusTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_dirname = tempfile.mkdtemp()
        self.sequence_path = os.path.join(self.tmp_dirname, 'test_seq.fasta')
        with open(self.sequence_path, 'w') as f:
            f.write('>dna1\nACGTACGTACGTACG\n')

    def tearDown(self):
        shutil.rmtree(self.tmp_dirname)

    def test_get_3_prime(self):
        dna1 = core.DnaSpeciesType(id='dna1', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=15, strand=core.PolymerStrand.positive)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(tu1.get_3_prime(), 15)

        dna1 = core.DnaSpeciesType(id='dna1', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=15, strand=core.PolymerStrand.negative)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(tu1.get_3_prime(), 1)

    def test_get_5_prime(self):

        dna1 = core.DnaSpeciesType(id='dna1', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=15, strand=core.PolymerStrand.positive)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(tu1.get_5_prime(), 1)

        dna1 = core.DnaSpeciesType(id='dna1', sequence_path=self.sequence_path)
        tu1 = prokaryote_schema.TranscriptionUnitLocus(
            id='tu1', polymer=dna1, start=1, end=15, strand=core.PolymerStrand.negative)
        rna1 = prokaryote_schema.RnaSpeciesType(
            id='rna1', name='rna1', transcription_units=[tu1])
        self.assertEqual(tu1.get_5_prime(), 15)

# only fake tests
class GeneLocusTestCase(unittest.TestCase):
    def test(self):
        gene = prokaryote_schema.GeneLocus(id='gene1', name='gene1',
                              symbol='gene_1', start=1, end=2)
        self.assertEqual(gene.id, 'gene1')
        self.assertEqual(gene.name, 'gene1')
        self.assertEqual(gene.symbol, 'gene_1')
        self.assertEqual(gene.start, 1)
        self.assertEqual(gene.end, 2)
