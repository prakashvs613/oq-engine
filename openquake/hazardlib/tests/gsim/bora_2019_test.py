# The Hazard Library
# Copyright (C) 2021 GEM Foundation
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

from openquake.hazardlib.gsim.bora_2019 import BoraEtAl2019
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Boraetal2019FASTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BoraEtAl2019

    # Tables computed using a python script provided by S.S. Bora.
    def test_mean(self):
        self.check('BCS19/FAS_log_mean.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('BCS19/FAS_intra.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('BCS19/FAS_total.csv',
                   max_discrep_percentage=0.1)
