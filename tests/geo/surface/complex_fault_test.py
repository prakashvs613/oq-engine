# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from nhlib.geo.point import Point
from nhlib.geo.line import Line
from nhlib.geo.surface.complex_fault import ComplexFaultSurface

from tests.geo.surface import _utils as utils


class ComplexFaultSurfaceCheckFaultDataTestCase(utils.SurfaceTestCase):
    def test_one_edge(self):
        edges = [Line([Point(0, 0), Point(0, 1)])]
        self.assertRaises(ValueError, ComplexFaultSurface.from_fault_data,
                          edges, mesh_spacing=1)

    def test_one_point_in_an_edge(self):
        edges = [Line([Point(0, 0), Point(0, 1)]),
                 Line([Point(0, 0, 1), Point(0, 1, 1)]),
                 Line([Point(0, 0, 2)])]
        self.assertRaises(ValueError, ComplexFaultSurface.from_fault_data,
                          edges, mesh_spacing=1)

    def test_non_positive_mesh_spacing(self):
        edges = [Line([Point(0, 0), Point(0, 1)]),
                 Line([Point(0, 0, 1), Point(0, 1, 1)])]
        self.assertRaises(ValueError, ComplexFaultSurface.from_fault_data,
                          edges, mesh_spacing=0)
        self.assertRaises(ValueError, ComplexFaultSurface.from_fault_data,
                          edges, mesh_spacing=-1)


class ComplexFaultFromFaultDataTestCase(utils.SurfaceTestCase):
    def test_1(self):
        edge1 = Line([Point(0, 0), Point(0.03, 0)])
        edge2 = Line([Point(0, 0, 2.224), Point(0.03, 0, 2.224)])
        surface = ComplexFaultSurface.from_fault_data([edge1, edge2],
                                                      mesh_spacing=1.112)
        self.assertIsInstance(surface, ComplexFaultSurface)
        self.assert_mesh_is(surface=surface, expected_mesh=[
            [(0, 0, 0), (0.01, 0, 0), (0.02, 0, 0), (0.03, 0, 0)],
            [(0, 0, 1.112), (0.01, 0, 1.112),
             (0.02, 0, 1.112), (0.03, 0, 1.112)],
            [(0, 0, 2.224), (0.01, 0, 2.224),
             (0.02, 0, 2.224), (0.03, 0, 2.224)],
        ])

    def test_2(self):
        edge1 = Line([Point(0, 0, 1), Point(0, 0.02, 1)])
        edge2 = Line([Point(0.02, 0, 0.5), Point(0.02, 0.01, 0.5)])
        edge3 = Line([Point(0, 0, 2), Point(0, 0.02, 2)])
        surface = ComplexFaultSurface.from_fault_data([edge1, edge2, edge3],
                                                      mesh_spacing=1)
        self.assert_mesh_is(surface=surface, expected_mesh=[
            [(0.00000000e+00, 0.00000000e+00, 1.00000000e+00),
             (0.00000000e+00, 1.00000000e-02, 1.00000000e+00),
             (0.00000000e+00, 2.00000000e-02, 1.00000000e+00)],

            [(8.70732572e-03, 5.33152318e-19, 7.82316857e-01),
             (8.67044753e-03, 7.83238825e-03, 7.83238813e-01),
             (8.57984833e-03, 1.57100762e-02, 7.85503798e-01)],

            [(1.74146514e-02, 1.06630462e-18, 5.64633714e-01),
             (1.73408950e-02, 5.66477632e-03, 5.66477626e-01),
             (1.71596963e-02, 1.14201520e-02, 5.71007595e-01)],

            [(1.47979150e-02, 3.18525318e-19, 8.90156376e-01),
             (1.48515919e-02, 6.28710212e-03, 8.86130608e-01),
             (1.49871315e-02, 1.25064345e-02, 8.75965152e-01)],

            [(7.39895749e-03, 7.71565830e-19, 1.44507819e+00),
             (7.42579599e-03, 8.14355113e-03, 1.44306530e+00),
             (7.49356586e-03, 1.62532174e-02, 1.43798258e+00)],

            [(0.00000000e+00, 0.00000000e+00, 2.00000000e+00),
             (0.00000000e+00, 1.00000000e-02, 2.00000000e+00),
             (0.00000000e+00, 2.00000000e-02, 2.00000000e+00)],
        ])

    def test_mesh_spacing_more_than_two_lengths(self):
        edge1 = Line([Point(0, 0, 0), Point(0, 0.1, 0)])
        edge2 = Line([Point(0, 0, 10), Point(0, 0.1, 20)])
        with self.assertRaises(ValueError) as ar:
            ComplexFaultSurface.from_fault_data([edge1, edge2],
                                                mesh_spacing=27)
        self.assertEqual(
            str(ar.exception),
            'mesh spacing 27.0 km is to big for mean length 13.0 km'
        )

    def test_mesh_spacing_more_than_two_widthss(self):
        edge1 = Line([Point(0, 0, 0), Point(0, 0.2, 0)])
        edge2 = Line([Point(0, 0, 10), Point(0, 0.2, 20)])
        with self.assertRaises(ValueError) as ar:
            ComplexFaultSurface.from_fault_data([edge1, edge2],
                                                mesh_spacing=30.1)
        self.assertEqual(
            str(ar.exception),
            'mesh spacing 30.1 km is to big for mean width 15.0 km'
        )
