import unittest
from openquake.nrmllib import valid


class ValidationTestCase(unittest.TestCase):

    def test_name(self):
        self.assertEqual(valid.name('x'), 'x')
        with self.assertRaises(ValueError):
            valid.name('1')
        with self.assertRaises(ValueError):
            valid.name('x y')

    def test_namelist(self):
        self.assertEqual(valid.namelist('x y'), ['x', 'y'])
        with self.assertRaises(ValueError):
            valid.namelist('')
        with self.assertRaises(ValueError):
            valid.namelist('x 1')

    def test_longitude(self):
        self.assertEqual(valid.longitude('1'), 1.0)
        self.assertEqual(valid.longitude('180'), 180.0)
        with self.assertRaises(ValueError):
            valid.longitude('181')
        with self.assertRaises(ValueError):
            valid.longitude('-181')

    def test_latitude(self):
        self.assertEqual(valid.latitude('1'), 1.0)
        self.assertEqual(valid.latitude('90'), 90.0)
        with self.assertRaises(ValueError):
            valid.latitude('91')
        with self.assertRaises(ValueError):
            valid.latitude('-91')

    def test_positiveint(self):
        self.assertEqual(valid.positiveint('1'), 1)
        with self.assertRaises(ValueError):
            valid.positiveint('-1')
        with self.assertRaises(ValueError):
            valid.positiveint('1.1')
        with self.assertRaises(ValueError):
            valid.positiveint('1.0')

    def test_positivefloat(self):
        self.assertEqual(valid.positiveint('1'), 1)
        with self.assertRaises(ValueError):
            valid.positivefloat('-1')
        self.assertEqual(valid.positivefloat('1.1'), 1.1)

    def test_probability(self):
        self.assertEqual(valid.probability('1'), 1.0)
        self.assertEqual(valid.probability('.5'), 0.5)
        self.assertEqual(valid.probability('0'), 0.0)
        with self.assertRaises(ValueError):
            valid.probability('1.1')
        with self.assertRaises(ValueError):
            valid.probability('-0.1')

    def test_IMTstr(self):
        self.assertEqual(valid.IMTstr('SA(1)'), ('SA', 1, 5))
        self.assertEqual(valid.IMTstr('SA(1.)'), ('SA', 1, 5))
        self.assertEqual(valid.IMTstr('SA(0.5)'), ('SA', 0.5, 5))
        self.assertEqual(valid.IMTstr('PGV'), ('PGV', None, None))
        with self.assertRaises(ValueError):
            valid.IMTstr('S(1)')
