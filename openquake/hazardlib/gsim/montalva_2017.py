# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module exports :class:`MontalvaEtAl2017SInter`
               :class:`MontalvaEtAl2017SSlab`
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.abrahamson_2015 import (
    AbrahamsonEtAl2015SInter, AbrahamsonEtAl2015SSlab, CONSTS,
    _compute_magterm)


# Period-Independent Coefficients (Table 2 of BC Hydro)
CONSTS = CONSTS.copy()
CONSTS["C1"] = 7.2


class MontalvaEtAl2017SInter(AbrahamsonEtAl2015SInter):
    """
    Adaptation of the Abrahamson et al. (2015) BC Hydro subduction interface
    GMPE, calibrated to Chilean strong motion data, by Montalva et al (2017)

    Montalval, G. A., Bastias, N., and Rodriguez-Marek, A. (2017) "Ground-
    Motion Prediction Equation for the Chilean Subduction Zone", Bulletin of
    the Seismological Society of America, 107(2), 901-911

    Note: This should be used in place of previous Montalva et al. (2016)
    implementation, as coefficients and model changed at the point of
    publication
    """

    def _compute_magnitude_term(self, C, dc1, mag):
        """
        Computes the magnitude scaling term given by equations (2) and (3)
        corrected by a local adjustment factor. Modified from original
        Abrahamson et al (2015) implementation as theta4 and theta5 are now
        period-dependent, whilst theta13 is now zero
        """
        return _compute_magterm(CONSTS['C1'], C['theta1'], C['theta4'],
                                C['theta5'], 0., dc1, mag)

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (4).
        Note this is overwriting the Abrahamson et al (2016) version as
        theta3 is now period dependent
        """
        return (C['theta2'] + C['theta3'] * (mag - CONSTS["C1"])) *\
            np.log(dists.rrup + CONSTS['c4'] * np.exp((mag - 6.) *
                   CONSTS['theta9'])) + (C['theta6'] * dists.rrup)

    # Coefficients table taken from electronic supplement to Montalva et al.
    # (2017)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt       vlin       b        theta1         theta2        theta3         theta4         theta5         theta6   theta7  theta8      theta10       theta11        theta12        theta13        theta14  theta15 theta16           phi           tau         sigma       phi_S2S
    pga      865.1  -1.186    5.87504394    -1.75359772    0.13125248     0.80276784    -0.33486952    -0.00039095   1.0988   -1.42   4.53143081    0.00567350     1.01494528     0.00000000    -0.73080261   0.9969   -1.00    0.69118080    0.47462209    0.83844918    0.56436373
    0.010    865.1  -1.186    5.87504394    -1.75359772    0.13125248     0.80276784    -0.33486952    -0.00039095   1.0988   -1.42   4.53143081    0.00567350     1.01494528     0.00000000    -0.73080261   0.9969   -1.00    0.69118080    0.47462209    0.83844918    0.56436373
    0.020    865.1  -1.186    5.97631438    -1.77010766    0.12246057     0.84131709    -0.28054559    -0.00038903   1.0988   -1.42   4.57416129    0.00565448     1.03738201     0.00000000    -0.73868917   0.9969   -1.00    0.69938258    0.47631913    0.84617723    0.57187735
    0.050   1053.5  -1.346    7.45297044    -2.03336398    0.08332151     1.03131243    -0.03954116     0.00000000   1.2536   -1.65   4.56070915    0.00848068     1.31034079     0.00000000    -0.69848828   1.1030   -1.18    0.70173433    0.53776165    0.88409200    0.57850117
    0.075   1085.7  -1.471    8.04759521    -2.10610081    0.08012671     1.03436999    -0.01295063    -0.00009638   1.4175   -1.80   4.36639286    0.00921589     1.48158019     0.00000000    -0.65335577   1.2732   -1.36    0.71412373    0.56188074    0.90867082    0.59936738
    0.100   1032.5  -1.624    7.76085108    -1.99370934    0.07303120     1.07565004     0.00758131    -0.00078515   1.3997   -1.80   3.90922953    0.00629627     1.65618649     0.00000000    -0.55051160   1.3042   -1.36    0.74112800    0.52707475    0.90943856    0.63409914
    0.150    877.6  -1.931    6.17191900    -1.58654201    0.05481839     1.17061492     0.10490549    -0.00267532   1.3582   -1.69   3.06236311    0.00558843     1.93944484     0.00000000    -0.42997222   1.2600   -1.30    0.74606525    0.50642417    0.90170882    0.63021739
    0.200    748.2  -2.188    4.83403302    -1.29711030    0.05249728     1.20531288     0.17968066    -0.00337590   1.1648   -1.49   3.50112817    0.00319554     2.08901131     0.00000000    -0.53087673   1.2230   -1.25    0.74515270    0.44618739    0.86852504    0.61699385
    0.250    654.3  -2.381    4.42687615    -1.18774055    0.02995137     1.37607187     0.22912175    -0.00355237   0.9940   -1.30   3.62815675    0.00181700     2.25003086     0.00000000    -0.58085678   1.1600   -1.17    0.72855743    0.45040229    0.85653847    0.58609155
    0.300    587.1  -2.518    4.57008643    -1.24895678    0.03865827     1.34990775     0.15592549    -0.00244847   0.8821   -1.18   3.87633808    0.00212947     2.28338700     0.00000000    -0.66280655   1.0500   -1.06    0.72093248    0.42549471    0.83713164    0.57014335
    0.400    503.0  -2.657    3.98311294    -1.13377346    0.04682762     1.37953880     0.11670946    -0.00207613   0.7046   -0.98   4.03388062    0.00068979     2.31408730     0.00000000    -0.72244113   0.8000   -0.78    0.71005053    0.42945015    0.82981877    0.54795548
    0.500    456.6  -2.669    4.86034340    -1.38019755    0.03822425     1.51949871     0.18347677    -0.00001896   0.5799   -0.82   4.31418239    0.00064780     2.33333479     0.00000000    -0.79644275   0.6620   -0.62    0.66934213    0.43333698    0.79737057    0.49113105
    0.600    430.3  -2.599    4.67510367    -1.35362409    0.02523729     1.66662746     0.21967977     0.00000000   0.5021   -0.70   4.75196667    0.00087070     2.23421777     0.00000000    -0.90120145   0.5800   -0.50    0.66733247    0.44599448    0.80264793    0.49077603
    0.750    410.5  -2.401    4.30862113    -1.30799859    0.00995253     1.85625091     0.29782648     0.00000000   0.3687   -0.54   4.70451938   -0.00031282     2.05217228     0.00000000    -0.89829099   0.4800   -0.34    0.66329494    0.46723155    0.81133563    0.48213254
    1.000    400.0  -1.955    3.57339281    -1.23082022    0.03605351     1.81217177     0.24372341     0.00000000   0.1746   -0.34   4.56020155   -0.00101097     1.63506217     0.00000000    -0.87330858   0.3300   -0.14    0.63504015    0.50143305    0.80914220    0.45955396
    1.500    400.0  -1.025    2.92216459    -1.18750273    0.02768934     2.03469107     0.22521403    -0.00009996  -0.0820   -0.05   4.83342978    0.00009741     0.69338467     0.00000000    -0.94685865   0.3100    0.00    0.60012607    0.51633193    0.79167542    0.42572864
    2.000    400.0  -0.299    2.39779653    -1.16319283    0.04011300     2.04340485     0.27382886    -0.00033356  -0.2821    0.12   4.59028522    0.00108512    -0.09761879     0.00000000    -0.90845421   0.3000    0.00    0.56961713    0.50688464    0.76249309    0.40178822
    2.500    400.0   0.000    1.64147667    -1.06543862    0.08310064     1.88987024     0.18739875    -0.00121364  -0.4108    0.25   4.13415056    0.00035459    -0.34931995     0.00000000    -0.80518214   0.3000    0.00    0.55384735    0.51465398    0.75605265    0.39825312
    3.000    400.0   0.000    1.66482796    -1.12677535    0.09403648     1.90503920     0.13268085    -0.00087595  -0.4466    0.30   4.18978319    0.00072950    -0.33269783     0.00000000    -0.81689247   0.3000    0.00    0.53658882    0.50365207    0.73593000    0.38493023
    4.000    400.0   0.000    0.90564754    -1.07619985    0.13838017     1.71178342     0.01379686    -0.00061861  -0.4344    0.30   4.50906779    0.00084112    -0.41320697     0.00000000    -0.87331394   0.3000    0.00    0.51345287    0.45311429    0.68479662    0.35578953
    5.000    400.0   0.000    0.61234440    -1.13079589    0.15259121     1.59358719     0.06464958     0.00000000  -0.4368    0.30   4.56385964    0.00068188    -0.42395126     0.00000000    -0.87800447   0.3000    0.00    0.51417184    0.43900131    0.67608789    0.34990851
    6.000    400.0   0.000    0.32672294    -1.15734380    0.12420910     1.69183532     0.32368231     0.00000000  -0.4586    0.30   4.55836575    0.00137322    -0.38759507     0.00000000    -0.88436295   0.3000    0.00    0.49080507    0.42084190    0.64652728    0.32047977
    7.500    400.0   0.000   -0.24139803    -1.14070070    0.10950824     1.71125604     0.60252124     0.00000000  -0.4433    0.30   5.08281865    0.00167053    -0.32638288     0.00000000    -0.98803311   0.3000    0.00    0.47063810    0.41701232    0.62880800    0.29895226
    10.00    400.0   0.000   -0.96313983    -1.09295336    0.11343926     1.67160339     0.77620830     0.00000000  -0.4828    0.30   5.49692364   -0.00070392    -0.25811162     0.00000000    -1.05008478   0.3000    0.00    0.46023151    0.38872242    0.60242690    0.28453650
    """)

    # Theoretically identical to the original Abrahamson et al. (2015)
    # correction, but in any case taken from Montalva et al. (2017) Matlab
    # code to ensure consistency with author's implementation
    COEFFS_MAG_SCALE = CoeffsTable(sa_damping=5, table="""\
    imt              dc1
    pga      0.200000000
    0.010    0.200000000
    0.020    0.200000000
    0.050    0.200000000
    0.075    0.200000000
    0.100    0.200000000
    0.150    0.200000000
    0.200    0.200000000
    0.250    0.200000000
    0.300    0.200000000
    0.400    0.143682921
    0.500    0.100000000
    0.600    0.073696559
    0.750    0.041503750
    1.000    0.000000000
    1.500   -0.058496250
    2.000   -0.100000000
    2.500   -0.155033971
    3.000   -0.200000000
    4.000   -0.200000000
    5.000   -0.200000000
    6.000   -0.200000000
    7.500   -0.200000000
    10.00   -0.200000000
    5.000   -0.200000000
    6.000   -0.200000000
    7.500   -0.200000000
    10.00   -0.200000000
    """)


class MontalvaEtAl2017SSlab(AbrahamsonEtAl2015SSlab):
    """
    Adaptation of the Abrahamson et al. (2015) BC Hydro subduction in-slab
    GMPE, calibrated to Chilean strong motion data
    """

    def _compute_magnitude_term(self, C, dc1, mag):
        """
        Computes the magnitude scaling term given by equations (2) and (3),
        corrected by a local adjustment factor - see documentation for
        interface version for changes
        """
        return _compute_magterm(CONSTS['C1'], C['theta1'], C['theta4'],
                                C['theta5'], 0., dc1, mag)

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (4)
        """
        return ((C['theta2'] + C['theta14'] + C['theta3'] *
                (mag - CONSTS["C1"])) *
                np.log(dists.rhypo + CONSTS['c4'] *
                np.exp((mag - 6.) * CONSTS['theta9'])) +
                (C['theta6'] * dists.rhypo)) + C["theta10"]

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt       vlin       b        theta1         theta2        theta3         theta4         theta5         theta6   theta7  theta8      theta10      theta11        theta12        theta13        theta14  theta15 theta16           phi           tau         sigma       phi_S2S
    pga      865.1  -1.186    5.87504394    -1.75359772    0.13125248     0.80276784    -0.33486952    -0.00039095   1.0988   -1.42   4.53143081    0.00567350     1.01494528     0.00000000    -0.73080261   0.9969   -1.00    0.69118080    0.47462209    0.83844918    0.56436373
    0.010    865.1  -1.186    5.87504394    -1.75359772    0.13125248     0.80276784    -0.33486952    -0.00039095   1.0988   -1.42   4.53143081    0.00567350     1.01494528     0.00000000    -0.73080261   0.9969   -1.00    0.69118080    0.47462209    0.83844918    0.56436373
    0.020    865.1  -1.186    5.97631438    -1.77010766    0.12246057     0.84131709    -0.28054559    -0.00038903   1.0988   -1.42   4.57416129    0.00565448     1.03738201     0.00000000    -0.73868917   0.9969   -1.00    0.69938258    0.47631913    0.84617723    0.57187735
    0.050   1053.5  -1.346    7.45297044    -2.03336398    0.08332151     1.03131243    -0.03954116     0.00000000   1.2536   -1.65   4.56070915    0.00848068     1.31034079     0.00000000    -0.69848828   1.1030   -1.18    0.70173433    0.53776165    0.88409200    0.57850117
    0.075   1085.7  -1.471    8.04759521    -2.10610081    0.08012671     1.03436999    -0.01295063    -0.00009638   1.4175   -1.80   4.36639286    0.00921589     1.48158019     0.00000000    -0.65335577   1.2732   -1.36    0.71412373    0.56188074    0.90867082    0.59936738
    0.100   1032.5  -1.624    7.76085108    -1.99370934    0.07303120     1.07565004     0.00758131    -0.00078515   1.3997   -1.80   3.90922953    0.00629627     1.65618649     0.00000000    -0.55051160   1.3042   -1.36    0.74112800    0.52707475    0.90943856    0.63409914
    0.150    877.6  -1.931    6.17191900    -1.58654201    0.05481839     1.17061492     0.10490549    -0.00267532   1.3582   -1.69   3.06236311    0.00558843     1.93944484     0.00000000    -0.42997222   1.2600   -1.30    0.74606525    0.50642417    0.90170882    0.63021739
    0.200    748.2  -2.188    4.83403302    -1.29711030    0.05249728     1.20531288     0.17968066    -0.00337590   1.1648   -1.49   3.50112817    0.00319554     2.08901131     0.00000000    -0.53087673   1.2230   -1.25    0.74515270    0.44618739    0.86852504    0.61699385
    0.250    654.3  -2.381    4.42687615    -1.18774055    0.02995137     1.37607187     0.22912175    -0.00355237   0.9940   -1.30   3.62815675    0.00181700     2.25003086     0.00000000    -0.58085678   1.1600   -1.17    0.72855743    0.45040229    0.85653847    0.58609155
    0.300    587.1  -2.518    4.57008643    -1.24895678    0.03865827     1.34990775     0.15592549    -0.00244847   0.8821   -1.18   3.87633808    0.00212947     2.28338700     0.00000000    -0.66280655   1.0500   -1.06    0.72093248    0.42549471    0.83713164    0.57014335
    0.400    503.0  -2.657    3.98311294    -1.13377346    0.04682762     1.37953880     0.11670946    -0.00207613   0.7046   -0.98   4.03388062    0.00068979     2.31408730     0.00000000    -0.72244113   0.8000   -0.78    0.71005053    0.42945015    0.82981877    0.54795548
    0.500    456.6  -2.669    4.86034340    -1.38019755    0.03822425     1.51949871     0.18347677    -0.00001896   0.5799   -0.82   4.31418239    0.00064780     2.33333479     0.00000000    -0.79644275   0.6620   -0.62    0.66934213    0.43333698    0.79737057    0.49113105
    0.600    430.3  -2.599    4.67510367    -1.35362409    0.02523729     1.66662746     0.21967977     0.00000000   0.5021   -0.70   4.75196667    0.00087070     2.23421777     0.00000000    -0.90120145   0.5800   -0.50    0.66733247    0.44599448    0.80264793    0.49077603
    0.750    410.5  -2.401    4.30862113    -1.30799859    0.00995253     1.85625091     0.29782648     0.00000000   0.3687   -0.54   4.70451938   -0.00031282     2.05217228     0.00000000    -0.89829099   0.4800   -0.34    0.66329494    0.46723155    0.81133563    0.48213254
    1.000    400.0  -1.955    3.57339281    -1.23082022    0.03605351     1.81217177     0.24372341     0.00000000   0.1746   -0.34   4.56020155   -0.00101097     1.63506217     0.00000000    -0.87330858   0.3300   -0.14    0.63504015    0.50143305    0.80914220    0.45955396
    1.500    400.0  -1.025    2.92216459    -1.18750273    0.02768934     2.03469107     0.22521403    -0.00009996  -0.0820   -0.05   4.83342978    0.00009741     0.69338467     0.00000000    -0.94685865   0.3100    0.00    0.60012607    0.51633193    0.79167542    0.42572864
    2.000    400.0  -0.299    2.39779653    -1.16319283    0.04011300     2.04340485     0.27382886    -0.00033356  -0.2821    0.12   4.59028522    0.00108512    -0.09761879     0.00000000    -0.90845421   0.3000    0.00    0.56961713    0.50688464    0.76249309    0.40178822
    2.500    400.0   0.000    1.64147667    -1.06543862    0.08310064     1.88987024     0.18739875    -0.00121364  -0.4108    0.25   4.13415056    0.00035459    -0.34931995     0.00000000    -0.80518214   0.3000    0.00    0.55384735    0.51465398    0.75605265    0.39825312
    3.000    400.0   0.000    1.66482796    -1.12677535    0.09403648     1.90503920     0.13268085    -0.00087595  -0.4466    0.30   4.18978319    0.00072950    -0.33269783     0.00000000    -0.81689247   0.3000    0.00    0.53658882    0.50365207    0.73593000    0.38493023
    4.000    400.0   0.000    0.90564754    -1.07619985    0.13838017     1.71178342     0.01379686    -0.00061861  -0.4344    0.30   4.50906779    0.00084112    -0.41320697     0.00000000    -0.87331394   0.3000    0.00    0.51345287    0.45311429    0.68479662    0.35578953
    5.000    400.0   0.000    0.61234440    -1.13079589    0.15259121     1.59358719     0.06464958     0.00000000  -0.4368    0.30   4.56385964    0.00068188    -0.42395126     0.00000000    -0.87800447   0.3000    0.00    0.51417184    0.43900131    0.67608789    0.34990851
    6.000    400.0   0.000    0.32672294    -1.15734380    0.12420910     1.69183532     0.32368231     0.00000000  -0.4586    0.30   4.55836575    0.00137322    -0.38759507     0.00000000    -0.88436295   0.3000    0.00    0.49080507    0.42084190    0.64652728    0.32047977
    7.500    400.0   0.000   -0.24139803    -1.14070070    0.10950824     1.71125604     0.60252124     0.00000000  -0.4433    0.30   5.08281865    0.00167053    -0.32638288     0.00000000    -0.98803311   0.3000    0.00    0.47063810    0.41701232    0.62880800    0.29895226
    10.00    400.0   0.000   -0.96313983    -1.09295336    0.11343926     1.67160339     0.77620830     0.00000000  -0.4828    0.30   5.49692364   -0.00070392    -0.25811162     0.00000000    -1.05008478   0.3000    0.00    0.46023151    0.38872242    0.60242690    0.28453650
    """)
