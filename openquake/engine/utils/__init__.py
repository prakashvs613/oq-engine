# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2016 GEM Foundation
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

import os
from openquake.baselib.performance import Monitor
from openquake.commonlib import valid
from openquake.engine import config

SOFT_MEM_LIMIT = int(config.get('memory', 'soft_mem_limit'))
HARD_MEM_LIMIT = int(config.get('memory', 'hard_mem_limit'))
USE_CELERY = valid.boolean(config.get('celery', 'use_celery') or 'false')

if USE_CELERY:
    os.environ['OQ_DISTRIBUTE'] = 'celery'

# NB: this import must go AFTER the setting of OQ_DISTRIBUTE
from openquake.commonlib import parallel

parallel.check_mem_usage.__defaults__ = (
    Monitor(), SOFT_MEM_LIMIT, HARD_MEM_LIMIT)


def confirm(prompt):
    """
    Ask for confirmation, given a ``prompt`` and return a boolean value.
    """
    while True:
        try:
            answer = raw_input(prompt)
        except KeyboardInterrupt:
            # the user presses ctrl+c, just say 'no'
            return False
        answer = answer.strip().lower()
        if answer not in ('y', 'n'):
            print 'Please enter y or n'
            continue
        return answer == 'y'
