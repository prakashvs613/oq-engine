#!/user/bin/env python
#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import csv
import codecs
from openquake.baselib import sap, performance
from openquake.hazardlib import nrml
from openquake.commonlib import readinput


@sap.Script
def expo2csv(job_ini):
    """
    Convert an exposure in XML format into CSV format
    """
    oq = readinput.get_oqparam(job_ini)
    exposure = readinput.get_exposure(oq)
    rows = []
    header = ['id', 'lon', 'lat', 'number']
    area = exposure.area['type'] != '?'
    if area:
        header.append('area')
    for costname in exposure.cost_types['name']:
        if costname != 'occupants':
            header.append(costname)
            if exposure.deductible_is_absolute is not None:
                header.append(costname + '-deductible')
            if exposure.insurance_limit_is_absolute is not None:
                header.append(costname + '-insured_limit')
    if exposure.retrofitted:
        header.append('retrofitted')
    header.extend(exposure.occupancy_periods)
    header.extend(exposure.tagcol.tagnames)
    for asset, asset_ref in zip(exposure.assets, exposure.asset_refs):
        row = [asset_ref.decode('utf8'), asset.location[0], asset.location[1],
               asset.number]
        if area:
            row.append(asset.area)
        for costname in exposure.cost_types['name']:
            if costname != 'occupants':
                row.append(asset.values[costname])
                if exposure.deductible_is_absolute is not None:
                    row.append(asset.deductibles[costname])
                if exposure.insurance_limit_is_absolute is not None:
                    row.append(asset.insurance_limits[costname])
        if exposure.retrofitted:
            row.append(asset._retrofitted)
        for time_event in exposure.occupancy_periods:
            row.append(asset.value(time_event))
        for tagname, tagidx in zip(exposure.tagcol.tagnames, asset.tagidxs):
            tags = getattr(exposure.tagcol, tagname)
            row.append(tags[tagidx])
        rows.append(row)

    with performance.Monitor('expo2csv') as mon:
        # save exposure data as csv
        csvname = oq.inputs['exposure'].replace('.xml', '.csv')
        print('Saving %s' % csvname)
        with codecs.open(csvname, 'wb', encoding='utf8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)

        # save exposure header as xml
        head = nrml.read(oq.inputs['exposure'], stop='assets')
        xmlname = oq.inputs['exposure'].replace('.xml', '-header.xml')
        print('Saving %s' % xmlname)
        head[0].assets.text = os.path.basename(csvname)
        with open(xmlname, 'wb') as f:
            nrml.write(head, f)
    print(mon)

expo2csv.arg('job_ini', 'path to the job.ini file')


if __name__ == '__main__':
    expo2csv.callfunc()
